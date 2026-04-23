def update_state_after_alloc(
        self,
        request: "Request",
        blocks: "KVCacheBlocks",
        num_external_tokens: int,
    ) -> None:
        req_id = request.request_id
        block_ids_by_group = blocks.get_block_ids()
        num_groups = len(block_ids_by_group)

        # Store tracking (eager mode only). Register the request;
        # block IDs are accumulated from scheduler_output in
        # _prepare_eager_store_specs via yield_req_data.
        if not self._lazy_mode and req_id not in self._reqs_to_store:
            self._reqs_to_store[req_id] = StoreRequestState(
                request=request,
                block_ids=tuple([] for _ in range(num_groups)),
                num_stored_blocks=[0] * num_groups,
            )

        if num_external_tokens == 0:
            return

        num_blocks_to_load = num_external_tokens // self.block_size
        assert num_blocks_to_load > 0

        skipped = sum(blk.block_hash is not None for blk in blocks.blocks[self.fa_gidx])
        num_computed_tokens = skipped * self.block_size
        hashes_to_load = request.block_hashes[skipped : skipped + num_blocks_to_load]

        # Find CPU cached blocks across all groups.
        max_hit_len = len(hashes_to_load) * self.block_size
        cpu_hit_blocks, hit_length = self.cpu_coordinator.find_longest_cache_hit(
            hashes_to_load, max_hit_len
        )
        assert hit_length == num_external_tokens, (
            f"Expected {num_external_tokens} hit tokens, got {hit_length}"
        )

        # Build transfer pairs across all groups.
        total_computed_tokens = num_computed_tokens + num_external_tokens
        kv_cache_groups = self.cpu_kv_cache_config.kv_cache_groups

        gpu_block_ids: list[int] = []
        cpu_block_ids: list[int] = []
        cpu_blocks_to_touch: list[KVCacheBlock] = []

        for g in range(num_groups):
            cpu_blocks_g = cpu_hit_blocks[g]
            n_ext_g = len(cpu_blocks_g)
            if n_ext_g == 0:
                continue

            # Number of blocks in the computed range for this group.
            g_block_size = kv_cache_groups[g].kv_cache_spec.block_size
            n_computed_g = cdiv(total_computed_tokens, g_block_size)

            # Back-trace: ext blocks sit at the tail of the computed range.
            gpu_ext_start = n_computed_g - n_ext_g
            group_gpu_ids = block_ids_by_group[g]

            for i, cpu_blk in enumerate(cpu_blocks_g):
                # Skip null blocks (e.g. sliding window or mamba padding).
                if cpu_blk.is_null:
                    continue
                gpu_block_ids.append(group_gpu_ids[gpu_ext_start + i])
                cpu_block_ids.append(cpu_blk.block_id)
                cpu_blocks_to_touch.append(cpu_blk)

        # Touch CPU blocks to prevent eviction during async load.
        self.cpu_block_pool.touch(cpu_blocks_to_touch)

        # Touch GPU blocks to prevent freeing during async load
        assert self._gpu_block_pool is not None
        self._gpu_block_pool.touch(
            [self._gpu_block_pool.blocks[bid] for bid in gpu_block_ids]
        )

        assert self._reqs_to_load.get(req_id) is None
        self._reqs_to_load[req_id] = LoadRequestState(
            request=request, transfer_meta=TransferMeta(gpu_block_ids, cpu_block_ids)
        )