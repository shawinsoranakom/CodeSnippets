def find_longest_cache_hit(
        cls,
        block_hashes: BlockHashList,
        max_length: int,
        kv_cache_group_ids: list[int],
        block_pool: BlockPool,
        kv_cache_spec: KVCacheSpec,
        use_eagle: bool,
        alignment_tokens: int,
        dcp_world_size: int = 1,
        pcp_world_size: int = 1,
    ) -> tuple[list[KVCacheBlock], ...]:
        assert isinstance(kv_cache_spec, MambaSpec), (
            "MambaManager can only be used for mamba groups"
        )
        assert dcp_world_size == 1, "DCP not support mamba now."
        assert pcp_world_size == 1, "PCP not support mamba now."
        computed_blocks: tuple[list[KVCacheBlock], ...] = tuple(
            [] for _ in range(len(kv_cache_group_ids))
        )

        block_size = kv_cache_spec.block_size
        max_num_blocks = max_length // block_size
        # Search from right to left and early stop when a match is found.
        for i in range(max_num_blocks - 1, -1, -1):
            if cached_block := block_pool.get_cached_block(
                block_hashes[i], kv_cache_group_ids
            ):
                # When enable Mamba prefix caching, `block_size` will be aligned
                # across full attention layers and Mamba layers to ensure the
                # prefix hit length aligned at block
                if (
                    block_size != alignment_tokens  # Faster for common case.
                    and (i + 1) * block_size % alignment_tokens != 0
                ):
                    continue
                for computed, cached in zip(computed_blocks, cached_block):
                    # the hit length logic later assumes:
                    #  hit_length = len(hit_blocks_other_attn[0])
                    #               * self.other_block_size
                    # so we insert dummy blocks at the beginning:
                    computed.extend([block_pool.null_block] * i)
                    computed.append(cached)
                break  # we just need the last match - early stopping

        return computed_blocks