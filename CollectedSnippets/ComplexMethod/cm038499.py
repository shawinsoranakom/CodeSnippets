def update_state_after_alloc(
        self, request: Request, blocks: KVCacheBlocks, num_external_tokens: int
    ):
        if num_external_tokens == 0:
            return

        req_status = self._req_status[request.request_id]
        block_groups = blocks.get_block_ids()

        # Below assertions will be removed once this function supports HMA
        assert len(self.config.kv_group_configs) == 1
        assert len(req_status.group_states) == 1
        assert len(block_groups) == 1
        block_ids = block_groups[0]
        group_config = self.config.kv_group_configs[0]
        group_state = req_status.group_states[0]

        num_computed_gpu_blocks = sum(
            block.block_hash is not None for block in blocks.blocks[0]
        )
        num_computed_tokens = num_computed_gpu_blocks * group_config.gpu_block_size
        full_block_tokens = num_computed_tokens + num_external_tokens
        assert full_block_tokens % group_config.offloaded_block_size == 0

        num_pending_gpu_blocks = len(block_ids) - num_computed_gpu_blocks
        assert (
            num_external_tokens == num_pending_gpu_blocks * group_config.gpu_block_size
        )

        start_block_idx = num_computed_tokens // group_config.offloaded_block_size
        num_blocks = full_block_tokens // group_config.offloaded_block_size

        assert len(request.block_hashes) // self.config.block_size_factor >= num_blocks
        offload_keys = group_state.offload_keys[start_block_idx:num_blocks]

        src_spec = self.manager.prepare_load(offload_keys, req_status.req_context)
        dst_spec = GPULoadStoreSpec(
            block_ids[num_computed_gpu_blocks:],
            group_sizes=(num_pending_gpu_blocks,),
            block_indices=(num_computed_gpu_blocks,),
        )

        self._reqs_to_load[request.request_id] = (src_spec, dst_spec)
        req_blocks_being_loaded = self._reqs_being_loaded[request.request_id]
        req_blocks_being_loaded.update(offload_keys)
        group_state.next_stored_block_idx = num_blocks

        if self._blocks_being_loaded is not None:
            self._blocks_being_loaded.update(req_blocks_being_loaded)