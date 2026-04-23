def _read_blocks_for_req(self, req_id: str, meta: ReqMeta):
        assert meta.remote is not None and self.transfer_topo is not None
        engine_id = meta.remote.engine_id
        remote_ranks = self.transfer_topo.target_remote_ranks(engine_id)
        remote_info = self.transfer_topo.get_engine_info(engine_id)
        tp_ratio = self.transfer_topo.tp_ratio(remote_info.remote_tp_size)

        if self._has_mamba:
            # Expand remote logical → kernel block IDs.
            meta.remote.block_ids = self._logical_to_remote_kernel_block_ids(
                meta.remote.block_ids,
                self._physical_blocks_per_logical[meta.remote.engine_id],
            )
        else:
            meta.remote.block_ids = self._logical_to_kernel_block_ids(
                meta.remote.block_ids
            )
        # D may have to perform multiple reads from different remote ranks.
        for i, remote_rank in enumerate(remote_ranks):
            if self.use_mla and tp_ratio < 0 and i > 0:
                # MLA opt: when P TP > D TP, only a single read is executed for
                # the first remote rank (cache is duplicated)..
                break

            remote_block_size = remote_info.remote_block_size
            logger.debug(
                "Remote agent %s available, calling _read_blocks"
                " on remote rank %s with remote block size %s for req %s",
                meta.remote.engine_id,
                remote_rank,
                remote_block_size,
                req_id,
            )
            # Get side handles.
            if tp_ratio < 0 and not self.use_mla:
                assert remote_block_size == self.block_size
                # Remote tp_size > local tp_size: we must perform multiple
                # reads. Get the memory chunk onto which we will write to.
                local_xfer_side_handle = self.src_xfer_handles_by_tp_ratio[tp_ratio][i]
            else:
                # Single read from remote, we write to the whole memory region.
                # Also handle remote block size different from local block size.
                local_xfer_side_handle = self.src_xfer_handles_by_block_size[
                    remote_block_size
                ]

            # Destination handle: remote_engine_id -> remote_rank -> handle.
            remote_xfer_side_handle = self.dst_xfer_side_handles[meta.remote.engine_id][
                remote_rank
            ]

            local_ids: BlockIds = meta.local_physical_block_ids
            remote_ids: BlockIds = meta.remote.block_ids
            if self._has_mamba:
                # Mamba-HMA: zero out FA groups for P ranks outside fa_read_targets.
                local_ids, remote_ids = self.transfer_topo.filter_block_ids_for_rank(
                    engine_id,
                    remote_rank,
                    local_ids,
                    remote_ids,
                    self._is_mamba_group,
                )

            self._read_blocks(
                request_id=req_id,
                dst_engine_id=meta.remote.engine_id,
                remote_request_id=meta.remote.request_id,
                local_block_ids=local_ids,
                remote_block_ids=remote_ids,
                remote_rank=remote_rank,
                local_xfer_side_handle=local_xfer_side_handle,
                remote_xfer_side_handle=remote_xfer_side_handle,
            )

            if self.use_mla and tp_ratio < 0:
                # ..but we still need to notify the other remote ranks that we
                # have the blocks we need so they can update the request state.
                notif_id = f"{req_id}:{self.world_size}".encode()
                remote_agents = self._remote_agents[meta.remote.engine_id]
                for rank_to_notify, agent in remote_agents.items():
                    if rank_to_notify != remote_rank:
                        self.nixl_wrapper.send_notif(agent, notif_msg=notif_id)