def _prepare_lazy_store_specs(
        self,
    ) -> tuple[list[int], list[int], list[str]]:
        """Single-pass cursor walk: offload cached GPU blocks near eviction.

        Walks the GPU free queue from the cursor, counting blocks that are
        free-or-offloaded (safe for the allocator to evict). Stops when
        target_free blocks are covered or CPU capacity is reached.
        """
        gpu_pool = self._gpu_block_pool
        if gpu_pool is None or self._target_free <= 0:
            return [], [], []

        free_queue = gpu_pool.free_block_queue
        cpu_pool = self.cpu_block_pool
        num_cpu_free = cpu_pool.get_num_free_blocks()

        # Validate cursor: stale if block was removed from free queue.
        if self._cursor is not None and self._cursor.ref_cnt > 0:
            self._cursor = None

        # Determine start node.
        if self._cursor is None:
            node = free_queue.fake_free_list_head.next_free_block
        else:
            node = self._cursor.next_free_block

        tail = free_queue.fake_free_list_tail
        gpu_ids: list[int] = []
        block_hashes: list[bytes] = []
        covered = 0
        last_visited = self._cursor

        while (
            node is not None
            and node is not tail
            and covered < self._target_free
            and len(gpu_ids) < num_cpu_free
        ):
            last_visited = node
            bhash = node.block_hash

            if (
                bhash is not None
                and not node.is_null
                and cpu_pool.cached_block_hash_to_block.get_one_block(bhash) is None
            ):
                gpu_ids.append(node.block_id)
                block_hashes.append(bhash)

            covered += 1
            node = node.next_free_block

        self._cursor = last_visited

        # Batch-allocate CPU blocks and stamp hashes.
        if gpu_ids:
            cpu_blocks = cpu_pool.get_new_blocks(len(gpu_ids))
            cpu_ids = [blk.block_id for blk in cpu_blocks]
            for cpu_blk, bhash in zip(cpu_blocks, block_hashes):  # type: ignore[assignment]
                cpu_blk._block_hash = bhash  # type: ignore[assignment]
            # Touch GPU blocks to prevent eviction during async copy.
            gpu_pool.touch([gpu_pool.blocks[bid] for bid in gpu_ids])
        else:
            cpu_ids = []

        return gpu_ids, cpu_ids, []