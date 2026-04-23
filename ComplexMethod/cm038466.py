def add_remote_agent(
        self,
        nixl_agent_meta: NixlAgentMetadata,
        remote_tp_rank: int = 0,
        remote_tp_size: int = 1,
    ) -> str:
        """
        Add the remote NIXL agent and prepare the descriptors for reading cache
        blocks from remote.

        In particular, handle both homogeneous and heterogeneous TP. The former
        requires local rank_i to read from remote rank_i.
        The latter, in the case of D.world_size < P.world_size, requires that a
        local (D) TP worker reads from multiple remote (P) TP workers.
        Conversely, assuming D.world_size > P.world_size, two or more local TP
        workers will read from a single remote TP worker.

        Here's an example for the last case described above (non-MLA):

        rank_offset     p_remote_tp_rank
        (kv split no)
        --------------------------------
            0                 0      Worker0  ---- 1st half of KV ----> Worker0  [ KV Cache ]
                                                                        /
            1                 0      Worker1  ---- 2nd half of KV -----/

            0                 1      Worker2  ---- 1st half of KV ----> Worker1  [ KV Cache ]
                                                                        /
            1                 1      Worker3  ---- 2nd half of KV -----/


                                Decoder TP workers                     Prefix TP workers
                                  (world_size=4)                         (world_size=2)
                                                 tp_ratio = 4 // 2 = 2

        Considering the KV Caches, if P-Worker_i has cache size [2, num_blocksP, kv_heads, block_size, head_dim]
        then D-Worker_j has [2, num_blocksD, kv_heads//tp_ratio, block_size, head_dim]. Mind the "HND" layout format.
        Assuming num_blocksD >= num_blocksP, D-Worker0 reads from P-Worker0 by preparing the kv_heads//tp_ratio
        first heads from all the slots of all the blocks. D-Worker1 will do the same, but reading the second split
        along the kv_heads dimension, and so forth until "tp_ratio" D TP workers have pulled from P-Worker0.

        Note that the above will also hold true for the homogeneous TP case, where tp_ratio evaluates to 1.

        Regarding MLA case, the cache is replicated across TP workers so the rank_offset will just always be 0
        so that the whole cache is shared by "tp_ratio" D TP workers.

        For Mamba hetero-TP, both tp_ratio > 0 (D_TP > P_TP) and
        tp_ratio < 0 (P_TP > D_TP) are supported by the 3-read transfer.
        """  # noqa: E501
        engine_id = nixl_agent_meta.engine_id
        # TODO re-evaluate refreshing for scaling/recovery
        if remote_tp_rank in self._remote_agents.get(engine_id, {}):
            logger.debug(
                "Remote agent with engine_id %s and rank"
                "%s already exchanged metadata, skip handshake.",
                engine_id,
                remote_tp_rank,
            )
            return self._remote_agents[engine_id][remote_tp_rank]

        ### Register remote engine in TransferTopology (idempotent).
        assert self.transfer_topo is not None
        transfer_topo = self.transfer_topo
        physical_blocks_per_logical = (
            compute_physical_blocks_per_logical(
                nixl_agent_meta.ssm_sizes,
                nixl_agent_meta.block_lens[0],
            )
            if self._has_mamba
            else 1
        )
        transfer_topo.register_remote_engine(
            remote_engine_id=engine_id,
            remote_tp_size=remote_tp_size,
            remote_block_size=nixl_agent_meta.block_size,
            remote_block_len=nixl_agent_meta.block_lens[0],
            remote_physical_blocks_per_logical=physical_blocks_per_logical,
            local_block_len=self.block_len_per_layer[0],
        )
        if self._has_mamba and engine_id not in self._physical_blocks_per_logical:
            self._physical_blocks_per_logical[engine_id] = physical_blocks_per_logical

        logger.info("Transfer plan: %s", transfer_topo.describe(engine_id))

        remote_agent_name = self.nixl_wrapper.add_remote_agent(
            nixl_agent_meta.agent_metadata
        )

        # Create dst descs and xfer side handles. TP workers have same #blocks
        # so we only register once per engine_id.
        # Example:
        # block_size_ratio > 1:
        # remote:               | 0| 1| 2| 3| 4| 5| 6| 7| 8| 9|10|11|12|
        # local origin:|          0|          1|          8|         12|
        # local mapped:| 0| 1| 2| 3| 4| 5| 6| 7| 8| 9|10|11|12|13|14|15|
        block_size_ratio = transfer_topo.block_size_ratio(nixl_agent_meta.block_size)

        if engine_id not in self.dst_num_blocks:
            self.dst_num_blocks[engine_id] = nixl_agent_meta.num_blocks

        # Keep track of remote agent kv caches base addresses.
        self.kv_caches_base_addr[engine_id][remote_tp_rank] = (
            nixl_agent_meta.kv_caches_base_addr
        )
        self._validate_remote_agent_handshake(nixl_agent_meta, remote_tp_size)

        # This is 1 when P and D `--tensor-parallel-size` match. Otherwise,
        # this is the ratio between the two sizes.
        tp_ratio = transfer_topo.tp_ratio(remote_tp_size)

        # Handle tp_size>num_kv_heads: replicate KV cache.
        indexes_into_remote = (
            not transfer_topo.replicates_kv_cache(engine_id) and tp_ratio > 0
        )

        logger.debug(
            "Registering remote agent (%s, rank %s) memory regions with tp_ratio %s",
            engine_id,
            remote_tp_rank,
            tp_ratio,
        )

        ### (Optional) Register local agent memory regions. MLA is not split.
        if (
            tp_ratio < 0
            and not self.use_mla
            and tp_ratio not in self.src_xfer_handles_by_tp_ratio
        ):
            # Remote tp_size > local tp_size: read from multiple remote ranks.
            # Logically "split" own regions into |tp_ratio| chunks. Mind that
            # we only do this once per remote tp_size (replica-friendly).
            abs_tp = -tp_ratio
            self.src_xfer_handles_by_tp_ratio[tp_ratio] = []

            if self._has_mamba:
                if transfer_topo.needs_split_handles(engine_id):
                    # Mamba-HMA: FA and Mamba use different split factors.
                    for handle_data in transfer_topo.compute_split_handle_data(
                        engine_id, self.src_blocks_data, self.num_descs, abs_tp
                    ):
                        descs = self.nixl_wrapper.get_xfer_descs(
                            handle_data, self.nixl_memory_type
                        )
                        handle = self.nixl_wrapper.prep_xfer_dlist(
                            "NIXL_INIT_AGENT", descs
                        )
                        self.src_xfer_handles_by_tp_ratio[tp_ratio].append(handle)

                    logger.info(
                        "Mamba-HMA split handles: %s, num_descs=%s",
                        transfer_topo.describe(engine_id),
                        self.num_descs,
                    )
            else:
                # Original path: uniform divide by abs_tp (non-Mamba-HMA).
                for i in range(abs_tp):
                    blocks_data = []
                    for memory_region in self.src_blocks_data:
                        addr, local_block_len, own_tp_rank = memory_region
                        remote_block_len = local_block_len // abs_tp
                        addr = addr + i * remote_block_len
                        blocks_data.append((addr, remote_block_len, own_tp_rank))
                    descs = self.nixl_wrapper.get_xfer_descs(
                        blocks_data, self.nixl_memory_type
                    )
                    handle = self.nixl_wrapper.prep_xfer_dlist("NIXL_INIT_AGENT", descs)
                    self.src_xfer_handles_by_tp_ratio[tp_ratio].append(handle)

        ### Register remote agent memory regions
        blocks_data = []
        # With homogeneous TP, D pulls the whole kv cache from corresponding
        # rank. With heterogeneous TP, prepare the descriptors by splitting the
        # P KV cache along kv_head dim, of D worker's kv_head size (D>P).
        # Eg. PTP1 DTP2 => P0 KV:[block0-KV_0 | block0-KV_1..].

        # Register all remote blocks, but only the corresponding kv heads.
        def register_remote_blocks(
            blocks_data: list[tuple[int, int, int]], mamba: bool
        ):
            for i, base_addr in enumerate(nixl_agent_meta.kv_caches_base_addr):
                # Read our whole local region size from remote.
                local_block_len = self.get_backend_aware_kv_block_len(
                    layer_idx=i, first_split=True, mamba_view=mamba
                )
                remote_kv_block_len = local_block_len // block_size_ratio
                if block_size_ratio > 1:
                    # using remote kv_block_len as transfer unit
                    local_block_len = remote_kv_block_len

                if tp_ratio < 0 and not self.use_mla:
                    # Remote tp is bigger: read a chunk of local region from remote
                    local_block_len = local_block_len // (-tp_ratio)
                rank_offset = (
                    self.tp_rank % tp_ratio * remote_kv_block_len
                    if indexes_into_remote
                    else 0
                )

                # Assume same num_blocks for mamba and fa
                num_blocks = (
                    nixl_agent_meta.num_blocks
                    if not mamba
                    else nixl_agent_meta.num_blocks
                    // self._physical_blocks_per_logical_kv_block
                )
                page_size = nixl_agent_meta.block_lens[i] * (
                    1 if not mamba else self._physical_blocks_per_logical_kv_block
                )
                for block_id in range(num_blocks):
                    block_offset = block_id * page_size
                    # For each block, grab the heads chunk belonging to rank_i
                    # of size remote_nheads // tp_ratio, which correspond to
                    # self.block_len == remote_block_len//tp_ratio bytes.
                    addr = base_addr + block_offset + rank_offset
                    # (addr, len, device id)
                    blocks_data.append(
                        (addr, local_block_len, nixl_agent_meta.device_id)
                    )

                if transfer_topo.is_kv_layout_blocks_first:
                    # With FlashInfer index V separately to allow head splitting.
                    second_split = self.get_backend_aware_kv_block_len(
                        layer_idx=i, first_split=False, mamba_view=mamba
                    )
                    # Apply the same scaling as local_block_len above for when we read
                    # a chunk of local V from `tp_ratio` separate remote workers.
                    if tp_ratio < 0 and not self.use_mla:
                        second_split = second_split // (-tp_ratio)
                    for block_id in range(num_blocks):
                        block_offset = block_id * page_size
                        addr = base_addr + block_offset + rank_offset
                        # Hop over the first split of remote page: either K or Conv.
                        if mamba:
                            v_addr = addr + nixl_agent_meta.ssm_sizes[0]
                        else:
                            v_addr = addr + nixl_agent_meta.block_lens[i] // 2
                        blocks_data.append(
                            (v_addr, second_split, nixl_agent_meta.device_id)
                        )

            logger.debug(
                "Created %s blocks for dst engine %s"
                " with remote rank %s and local rank %s",
                len(blocks_data),
                engine_id,
                remote_tp_rank,
                self.tp_rank,
            )

        if self._has_mamba:
            # Mamba-HMA: separate FA registration with GQA-aware sizing,
            # plus mamba 3-read registration for the Mamba "view" of the
            # same KV cache tensors.
            logger.debug(
                "Registering remote Mamba blocks for engine %s rank %s",
                engine_id,
                remote_tp_rank,
            )
            blocks_data.extend(
                self._build_fa_remote_for_mamba(
                    nixl_agent_meta,
                    block_size_ratio,
                    transfer_topo,
                    engine_id,
                )
            )
            blocks_data.extend(
                self._build_mamba_remote(
                    nixl_agent_meta,
                    tp_ratio,
                )
            )
        else:
            register_remote_blocks(blocks_data, mamba=False)

        # Register with NIXL.
        descs = self.nixl_wrapper.get_xfer_descs(blocks_data, self.nixl_memory_type)
        self.dst_xfer_side_handles[engine_id][remote_tp_rank] = (
            self.nixl_wrapper.prep_xfer_dlist(remote_agent_name, descs)
        )

        if block_size_ratio > 1:
            # when prefill with smaller block_size, we need to init a
            # new handler with same block_len to match
            self.src_xfer_handles_by_block_size[nixl_agent_meta.block_size] = (
                self.register_local_xfer_handler(nixl_agent_meta.block_size)[0]
            )

        return remote_agent_name