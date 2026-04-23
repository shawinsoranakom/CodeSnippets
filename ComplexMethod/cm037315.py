def allocate_new_computed_blocks(
        self,
        request_id: str,
        new_computed_blocks: Sequence[KVCacheBlock],
        num_local_computed_tokens: int,
        num_external_computed_tokens: int,
    ) -> None:
        """
        Add the new computed blocks to the request. This involves three steps:
        1. Touch the computed blocks to make sure they won't be evicted.
        1.5. (Optional) For sliding window, skip blocks are padded with null blocks.
        2. Add the remaining computed blocks.
        3. (Optional) For KV connectors, allocate new blocks for external computed
            tokens (if any).

        Args:
            request_id: The request ID.
            new_computed_blocks: The new computed blocks just hitting the
                prefix cache.
            num_local_computed_tokens: The number of local computed tokens.
            num_external_computed_tokens: The number of external computed tokens.
        """

        if request_id in self.num_cached_block:
            # Fast-path: a running request won't have any new prefix-cache hits.
            # It should not have any new computed blocks.
            assert len(new_computed_blocks) == 0
            return

        # A new request.
        req_blocks = self.req_to_blocks[request_id]
        assert len(req_blocks) == 0
        num_total_computed_tokens = (
            num_local_computed_tokens + num_external_computed_tokens
        )
        num_skipped_tokens = self.get_num_skipped_tokens(num_total_computed_tokens)
        num_skipped_blocks = num_skipped_tokens // self.block_size
        if num_skipped_blocks > 0:
            # It is possible that all new computed blocks are skipped when
            # num_skipped_blocks > len(new_computed_blocks).
            new_computed_blocks = new_computed_blocks[num_skipped_blocks:]
            # Some external computed tokens may be skipped too.
            num_external_computed_tokens = min(
                num_total_computed_tokens - num_skipped_tokens,
                num_external_computed_tokens,
            )

        # Touch the computed blocks to make sure they won't be evicted.
        if self.enable_caching:
            self.block_pool.touch(new_computed_blocks)
        else:
            assert not any(new_computed_blocks), (
                "Computed blocks should be empty when prefix caching is disabled"
            )

        # Skip blocks are padded with null blocks.
        req_blocks.extend([self._null_block] * num_skipped_blocks)
        # Add the remaining computed blocks.
        req_blocks.extend(new_computed_blocks)
        # All cached hits (including skipped nulls) are already cached; mark
        # them so cache_blocks() will not try to re-cache blocks that already
        # have a block_hash set.
        self.num_cached_block[request_id] = len(req_blocks)

        if num_external_computed_tokens > 0:
            # Allocate new blocks for external computed tokens.
            allocated_blocks = self.block_pool.get_new_blocks(
                cdiv(num_total_computed_tokens, self.block_size) - len(req_blocks)
            )
            req_blocks.extend(allocated_blocks)
            if type(self.kv_cache_spec) in (FullAttentionSpec, TQFullAttentionSpec):
                self.new_block_ids.extend(b.block_id for b in allocated_blocks)