def find_longest_cache_hit(
        self,
        block_hashes: list[BlockHash],
        max_cache_hit_length: int,
    ) -> tuple[tuple[list[KVCacheBlock], ...], int]:
        """
        Find the longest cache hit using an iterative fixed-point algorithm.

        Each attention type either accepts the current candidate length or
        reduces it. If any type reduces the length, restart checks over all
        types. This converges because length monotonically decreases and is
        bounded below by 0.

        Args:
            block_hashes: The block hashes of the request.
            max_cache_hit_length: The maximum length of the cache hit.

        Returns:
            A tuple containing:
                - A tuple of the cache hit blocks for each single type manager.
                - The number of tokens of the longest cache hit.
        """

        def _get_block_hashes(kv_cache_spec: KVCacheSpec) -> BlockHashList:
            if kv_cache_spec.block_size == self.hash_block_size:
                return block_hashes
            return BlockHashListWithBlockSize(
                block_hashes, self.hash_block_size, kv_cache_spec.block_size
            )

        num_groups = len(self.kv_cache_config.kv_cache_groups)
        hit_length = max_cache_hit_length
        hit_blocks_by_group: list[list[KVCacheBlock] | None] = [None] * num_groups

        # Simple hybrid (1 full attn + 1 other): one iteration suffices.
        # Full attn is always first if it exists. This avoids EAGLE drops
        # being applied multiple times to non-full-attn groups.
        # FIXME (yifan): However, for complex hybrid models with multiple attn
        # groups, we still have the EAGLE spiral block dropping problem. See
        # discussion in issue https://github.com/vllm-project/vllm/issues/32802.
        is_simple_hybrid = len(self.attention_groups) == 2 and isinstance(
            self.attention_groups[0][0], FullAttentionSpec
        )

        while True:
            curr_hit_length = hit_length

            for spec, group_ids, manager_cls in self.attention_groups:
                is_full_attn = isinstance(spec, FullAttentionSpec)

                # Full attention: reuse cached blocks (downward-closed property)
                cached_blocks = hit_blocks_by_group[group_ids[0]]
                if is_full_attn and cached_blocks is not None:
                    # For full attention, we only need to compute the cache hit
                    # length once. Starting from the second iteration, if the
                    # curr_hit_length is reduced by other groups, we can simply
                    # keep the first (curr_hit_length // block_size) blocks from
                    # the last iteration.
                    num_blocks = curr_hit_length // spec.block_size
                    curr_hit_length = num_blocks * spec.block_size
                else:
                    hit_blocks = manager_cls.find_longest_cache_hit(
                        block_hashes=_get_block_hashes(spec),
                        max_length=curr_hit_length,
                        kv_cache_group_ids=group_ids,
                        block_pool=self.block_pool,
                        kv_cache_spec=spec,
                        use_eagle=self.use_eagle,
                        alignment_tokens=self.lcm_block_size,
                    )
                    curr_hit_length = len(hit_blocks[0]) * spec.block_size
                    for group_id, blocks in zip(group_ids, hit_blocks):
                        hit_blocks_by_group[group_id] = blocks

            if curr_hit_length >= hit_length:
                break
            hit_length = curr_hit_length
            # Simple hybrid: exit after one iteration
            if is_simple_hybrid:
                break

        # Truncate full attention blocks to final hit_length (if present)
        spec, group_ids, _ = self.attention_groups[0]
        if isinstance(spec, FullAttentionSpec):
            num_blocks = hit_length // spec.block_size
            for group_id in group_ids:
                if (blks := hit_blocks_by_group[group_id]) is not None:
                    del blks[num_blocks:]

        return tuple(
            blocks if blocks is not None else [] for blocks in hit_blocks_by_group
        ), hit_length