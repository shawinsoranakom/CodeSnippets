def _read_blocks(
        self,
        local_block_ids: BlockIds,
        remote_block_ids: BlockIds,
        dst_engine_id: str,
        request_id: str,
        remote_request_id: str,
        remote_rank: int,
        local_xfer_side_handle: int,
        remote_xfer_side_handle: int,
    ):
        """
        Post a READ point-to-point xfer request from a single local worker to
        a single remote worker.
        """
        assert self.transfer_topo is not None
        remote_info = self.transfer_topo.get_engine_info(dst_engine_id)
        block_size_ratio = self.transfer_topo.block_size_ratio(
            remote_info.remote_block_size
        )
        if block_size_ratio > 1:
            # TODO (NickLucche) assume HMA is off. Change to handle multiple KV groups.
            assert not self._is_hma_required
            local_block_ids0 = local_block_ids[0] if local_block_ids else []
            remote_block_ids0 = remote_block_ids[0]
            local_block_ids_mapped = self.get_mapped_blocks(
                np.asarray(local_block_ids0), block_size_ratio
            ).tolist()
            if len(local_block_ids_mapped) > len(remote_block_ids0):
                # NOTE:
                # get_mapped_blocks will always expand block_ids for n times.
                # ex:
                # prefill block_ids with block_size as 4:
                # [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                # Local decode block_ids with block_size as 16: [1, 2, 3]
                # expanded decode block_ids with get_mapped_blocks from [1, 2, 3] to
                # [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12]
                # Then we clip local to align with prefill
                # [1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12] to
                # [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
                local_block_ids_mapped = local_block_ids_mapped[
                    : len(remote_block_ids0)
                ]
            local_block_ids = [local_block_ids_mapped] if local_block_ids_mapped else []
            remote_block_ids = [remote_block_ids0]
        # NOTE(rob): having the staging blocks be on the READER side is
        # not going to work well (since we will have to call rearrange tensors).
        # after we detect the txn is complete (which means we cannot make the
        # read trxn async easily). If we want to make "READ" happen cleanly,
        # then we will need to have the staging blocks on the remote side.

        # NOTE(rob): according to nvidia the staging blocks are used to
        # saturate IB with heterogeneous TP sizes.

        # Number of D TP workers that will read from dst P. Propagate info
        # on notification so that dst worker can wait before freeing blocks.
        notif_id = f"{remote_request_id}:{self.world_size}".encode()

        # Full prefix cache hit: do not need to read remote blocks,
        # just notify P worker that we have the blocks we need.
        if len(local_block_ids) == 0:
            # A full prefix cache hit is indicated with an empty list.
            agent_name = self._remote_agents[dst_engine_id][remote_rank]
            try:
                self.nixl_wrapper.send_notif(agent_name, notif_msg=notif_id)
            except Exception as e:
                self._log_failure(
                    failure_type="notification_failed",
                    msg="P worker blocks will be freed after timeout. "
                    "This may indicate network issues.",
                    req_id=request_id,
                    error=e,
                    dst_engine_id=dst_engine_id,
                    remote_rank=remote_rank,
                    remote_agent_name=agent_name,
                )
                self.xfer_stats.record_failed_notification()
            return

        assert (
            len(remote_block_ids)
            == len(local_block_ids)
            == len(self.kv_cache_config.kv_cache_groups)
        )
        remote_block_ids = list(remote_block_ids)
        for i, remote_group in enumerate(remote_block_ids):
            num_remote_blocks = len(remote_group)
            num_local_blocks = len(local_block_ids[i])
            if not self._is_mamba_group[i]:
                assert num_local_blocks <= num_remote_blocks
            # Partial prefix cache hit: just read uncomputed blocks.
            # Skip mamba groups — their blocks represent full state (conv+ssm),
            # not per-token data, so trimming would corrupt the transfer.
            if num_local_blocks < num_remote_blocks and not self._is_mamba_group[i]:
                remote_block_ids[i] = remote_group[-num_local_blocks:]

        # NOTE (nicolo) With homogeneous TP, each TP worker loads KV from
        # corresponding rank. With heterogeneous TP, fixing D>P, the D tp
        # workers will issue xfers to parts of the P worker remote kv caches.

        # Get descs ids.
        remote_block_descs_ids = self._get_block_descs_ids(
            dst_engine_id,
            remote_block_ids,
        )
        local_block_descs_ids = self._get_block_descs_ids(
            self.engine_id,
            local_block_ids,
            block_size_ratio=block_size_ratio,
        )

        assert len(local_block_descs_ids) == len(remote_block_descs_ids)

        # Prepare transfer with Nixl.
        handle = None
        try:
            handle = self.nixl_wrapper.make_prepped_xfer(
                "READ",
                local_xfer_side_handle,
                local_block_descs_ids,
                remote_xfer_side_handle,
                remote_block_descs_ids,
                notif_msg=notif_id,
            )

            # Begin async xfer.
            self.nixl_wrapper.transfer(handle)

            # Use handle to check completion in future step().
            self._recving_transfers[request_id].append(handle)
        except Exception as e:
            # mark all (logical) blocks for this request as invalid
            self._log_failure(
                failure_type="transfer_setup_failed",
                req_id=request_id,
                msg="Marking blocks as invalid",
                error=e,
                dst_engine_id=dst_engine_id,
                remote_rank=remote_rank,
            )
            if (
                meta := self._recving_metadata.get(request_id)
            ) and not self._is_hma_required:
                self._invalid_block_ids.update(meta.local_block_ids[0])
            self.xfer_stats.record_failed_transfer()
            if handle is not None:
                self.nixl_wrapper.release_xfer_handle(handle)
            self._failed_recv_reqs.add(request_id)