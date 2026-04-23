def transfer_async(self, job_id: int, transfer_spec: TransferSpec) -> bool:
        src_spec, dst_spec = transfer_spec
        assert isinstance(src_spec, BlockIDsLoadStoreSpec)
        assert isinstance(dst_spec, BlockIDsLoadStoreSpec)

        src_blocks = src_spec.block_ids
        dst_blocks = dst_spec.block_ids
        assert src_blocks.ndim == 1
        assert dst_blocks.ndim == 1

        num_src_blocks = len(src_blocks)
        num_dst_blocks = len(dst_blocks)

        # There are 2 types of transfers:
        # 1. GPU -> CPU
        # 2. CPU -> GPU
        #
        # transfers are also to CPU blocks, EXCEPT MAYBE for the first and last block.
        # i.e. the first and last CPU blocks in src_blocks can match against
        # a smaller (byte-wise) set of GPU blocks in dst_blocks.
        # In such cases, we may need to skip some gpu-sized sub-blocks,
        # and start reading/writing from the middle of the first CPU block.
        # If we have multiple KV cache groups (when using HMA with hybrid models),
        # we may have a partial first/last CPU block per each group.
        # The group_sizes parameter encodes the size of each group of blocks
        # in the GPU dst_blocks.
        # If group_sizes is None, we assume all blocks belong to a single group.
        # The logical_offset parameter maps each group of blocks to its logical
        # offset inside the request, counting in GPU blocks.
        # This allows us to find the correct starting position
        # in the matching first CPU block.

        # extract group_sizes from the GPU spec
        gpu_spec = src_spec if self.gpu_to_cpu else dst_spec
        assert isinstance(gpu_spec, GPULoadStoreSpec)
        group_sizes = gpu_spec.group_sizes
        assert len(group_sizes) == len(self.kv_cache_groups_data_refs)

        # extract block indices from the GPU spec
        block_indices = gpu_spec.block_indices
        assert len(block_indices) == len(self.kv_cache_groups_data_refs)

        num_copy_ops = 0
        for group_size, group_data_refs in zip(
            group_sizes, self.kv_cache_groups_data_refs
        ):
            num_copy_ops += group_size * len(group_data_refs)

        all_src = np.empty(num_copy_ops, dtype=np.int64)
        all_dst = np.empty(num_copy_ops, dtype=np.int64)
        all_sizes = np.empty(num_copy_ops, dtype=np.int64)

        src_offset = 0
        dst_offset = 0
        op_idx = 0
        # count total number of bytes copied
        num_transfer_bytes = 0
        for group_size, block_idx, group_data_refs in zip(
            group_sizes, block_indices, self.kv_cache_groups_data_refs
        ):
            if group_size == 0:
                continue

            src_logical_blocks_to_skip = block_idx % self.src_block_size_factor
            dst_logical_blocks_to_skip = block_idx % self.dst_block_size_factor
            src_logical_blocks_count = group_size + src_logical_blocks_to_skip
            dst_logical_blocks_count = group_size + dst_logical_blocks_to_skip

            dst_blocks_count = cdiv(
                dst_logical_blocks_count, self.dst_block_size_factor
            )
            dst_end_offset = dst_offset + dst_blocks_count
            assert dst_end_offset <= num_dst_blocks

            src_blocks_count = cdiv(
                src_logical_blocks_count, self.src_block_size_factor
            )
            src_end_offset = src_offset + src_blocks_count
            assert src_end_offset <= num_src_blocks

            group_src = src_blocks[src_offset:src_end_offset]
            group_dst = dst_blocks[dst_offset:dst_end_offset]

            for data_ref in group_data_refs:
                t_idx = data_ref.tensor_idx
                end_idx = op_idx + group_size

                compute_sub_block_ptrs(
                    group_src,
                    self.src_block_size_factor,
                    all_src[op_idx:end_idx],
                    self.src_tensors[t_idx],
                    skip_count=src_logical_blocks_to_skip,
                )
                compute_sub_block_ptrs(
                    group_dst,
                    self.dst_block_size_factor,
                    all_dst[op_idx:end_idx],
                    self.dst_tensors[t_idx],
                    skip_count=dst_logical_blocks_to_skip,
                )

                all_sizes[op_idx:end_idx] = data_ref.page_size_bytes
                num_transfer_bytes += group_size * data_ref.page_size_bytes
                op_idx = end_idx

            src_offset = src_end_offset
            dst_offset = dst_end_offset

        assert src_offset == num_src_blocks
        assert dst_offset == num_dst_blocks
        assert op_idx == num_copy_ops

        batch_src = torch.from_numpy(all_src)
        batch_dst = torch.from_numpy(all_dst)
        batch_sizes = torch.from_numpy(all_sizes)

        stream = self._stream_pool.pop() if self._stream_pool else torch.cuda.Stream()
        start_event = (
            self._event_pool.pop()
            if self._event_pool
            else torch.Event(enable_timing=True)
        )
        end_event = (
            self._event_pool.pop()
            if self._event_pool
            else torch.Event(enable_timing=True)
        )

        if self.gpu_to_cpu:
            # wait for model computation to finish before offloading
            stream.wait_stream(torch.cuda.current_stream())
        if self._transfers:
            last_transfer: Transfer = self._transfers[-1]
            last_event = last_transfer.end_event
            # assure job will start only after the previous one completes
            stream.wait_event(last_event)
        with torch.cuda.stream(stream):
            start_event.record(stream)
            if num_copy_ops > 0:
                ops.swap_blocks_batch(batch_src, batch_dst, batch_sizes)
            end_event.record(stream)

        self._transfer_events[job_id] = end_event
        self._transfers.append(
            Transfer(
                job_id=job_id,
                stream=stream,
                start_event=start_event,
                end_event=end_event,
                num_bytes=num_transfer_bytes,
            )
        )

        # success
        return True