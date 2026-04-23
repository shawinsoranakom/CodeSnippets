async def _build_transfer_params(
        self,
        ready_reqs: list[tuple[ReqId, SendBlockMeta]],
        agent_meta: MooncakeXferMetadata,
        local_regions: list[TransferRegion],
        remote_regions: list[TransferRegion],
    ) -> tuple[list[int], list[int], list[int], list[ReqId], str | None]:
        src_ptrs = []
        dst_ptrs = []
        lengths = []
        err_reqs: list[ReqId] = []
        err_msg: str | None = None
        remote_session = f"{agent_meta.remote_hostname}:{agent_meta.remote_port}"

        for d_req_id, send_meta in ready_reqs:
            _, remote_block_ids = agent_meta.req_blocks[d_req_id]
            num_remote_blocks = len(remote_block_ids)
            if num_remote_blocks == 0:
                continue

            local_block_ids = send_meta.local_block_ids
            # Partial prefix cache hit: just read uncomputed blocks.
            num_local_blocks = len(local_block_ids)
            if num_local_blocks < num_remote_blocks:
                logger.error(
                    "req %s: local blocks(%d) less than remote blocks(%d)!",
                    d_req_id,
                    num_local_blocks,
                    num_remote_blocks,
                )
                err_reqs.append(d_req_id)
                if err_msg is None:
                    err_msg = "P num blocks less than D"
                continue
            if num_local_blocks > num_remote_blocks:
                local_block_ids = local_block_ids[-num_remote_blocks:]

            # Group by indices
            group_local_block_ids, group_remote_block_ids = group_concurrent_contiguous(
                local_block_ids, remote_block_ids
            )

            for local_region, remote_region in zip(local_regions, remote_regions):
                should_transfer, src_region_offset, dst_region_offset, transfer_len = (
                    self._get_sender_transfer_plan(
                        local_kv_block_len=local_region.kv_block_len,
                        remote_kv_block_len=remote_region.kv_block_len,
                        remote_tp_rank=agent_meta.remote_tp_rank,
                        remote_tp_size=agent_meta.remote_tp_size,
                    )
                )
                if not should_transfer:
                    # Replicated KV cache: only one producer rank in the TP group
                    # needs to send the actual bytes for this paired decoder rank.
                    # TODO: Account for replicated producer KV in
                    # get_target_remote_ranks() so we can avoid sending
                    # unnecessary ZMQ requests and remove this branch.
                    continue

                assert src_region_offset + transfer_len <= local_region.kv_block_len, (
                    "Computed source transfer region exceeds local KV block size."
                )
                assert dst_region_offset + transfer_len <= remote_region.kv_block_len, (
                    "Computed destination transfer region exceeds remote KV block size."
                )
                # Collapse one contiguous block group into a single larger
                # transfer descriptor when the per-block copy is identical.
                can_coalesce = _can_coalesce_block_transfers(
                    local_region_block_len=local_region.block_len,
                    remote_region_block_len=remote_region.block_len,
                    src_region_offset=src_region_offset,
                    dst_region_offset=dst_region_offset,
                    transfer_len=transfer_len,
                )

                for group_local_block_id, group_remote_block_id in zip(
                    group_local_block_ids, group_remote_block_ids
                ):
                    if can_coalesce:
                        src_ptrs.append(
                            local_region.base_addr
                            + group_local_block_id[0] * local_region.block_len
                            + src_region_offset
                        )
                        dst_ptrs.append(
                            remote_region.base_addr
                            + group_remote_block_id[0] * remote_region.block_len
                            + dst_region_offset
                        )
                        lengths.append(transfer_len * len(group_local_block_id))
                    else:
                        for local_block_id, remote_block_id in zip(
                            group_local_block_id, group_remote_block_id
                        ):
                            src_ptrs.append(
                                local_region.base_addr
                                + local_block_id * local_region.block_len
                                + src_region_offset
                            )
                            dst_ptrs.append(
                                remote_region.base_addr
                                + remote_block_id * remote_region.block_len
                                + dst_region_offset
                            )
                            lengths.append(transfer_len)

                if local_region is local_regions[0]:
                    logger.debug(
                        "Mooncake transfer plan for request %s: local_tp=%d "
                        "remote_tp=%d remote_tp_rank=%d local_block_len=%d "
                        "remote_block_len=%d src_offset=%d dst_offset=%d "
                        "transfer_len=%d coalesce=%s",
                        d_req_id,
                        self.tp_size,
                        agent_meta.remote_tp_size,
                        agent_meta.remote_tp_rank,
                        local_region.block_len,
                        remote_region.block_len,
                        src_region_offset,
                        dst_region_offset,
                        transfer_len,
                        can_coalesce,
                    )

            logger.debug(
                "Sending kv_caches for request %s (%d blocks) to %s",
                d_req_id,
                num_remote_blocks,
                remote_session,
            )

        return src_ptrs, dst_ptrs, lengths, err_reqs, err_msg