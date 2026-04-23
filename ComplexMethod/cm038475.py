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