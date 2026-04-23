def _build_block_mask_direct(self) -> BlockMask:
        """Direct block mask construction for paged KV cache attention.

        This method constructs the block mask directly using
        BlockMask.from_kv_blocks which is much more efficient than the
        generic create_block_mask approach.

        The direct path works as follows:
        1. For each query token, fetch blocks from block_table using max_seq_len
           and exclude out of sliding window blocks if needed.
           (this fetches more blocks than needed for shorter sequences)
        2. Group query tokens into chunks of q_block_size
        3. For each group, deduplicate the blocks using unique_static_unsorted
        4. Create BlockMask using the deduplicated block indices

        Over-estimation occurs when a group of q_block_size tokens contains
        multiple sequence IDs (doc_ids). In this case, we fetch ALL blocks for
        each sequence represented in the group, even though individual query
        tokens may only need a subset of those blocks based on causal masking
        and their position.

        """
        page_to_block_ratio = self.kv_block_size // self.block_size
        if page_to_block_ratio != 1:
            raise ValueError(
                f"FlexAttention currently requires the cache block size "
                f"({self.block_size}) to be equal to the kv_block_size "
                f"({self.kv_block_size}). Please check your model's "
                f"configuration."
            )

        used_pages = self.block_table[
            self.doc_ids, : cdiv(self.max_seq_len, self.block_size)
        ]

        custom_hint = self.block_sparsity_hint is not None

        if self.sliding_window or custom_hint:
            device = used_pages.device
            assert self.doc_ids is not None
            token_indices = torch.arange(
                self.doc_ids.shape[0], device=device, dtype=torch.long
            )
            logical_q_idx = (
                token_indices
                - self.query_start_loc[self.doc_ids]
                + self.decode_offset[self.doc_ids]
            )

            if self.sliding_window:
                assert self.sliding_window is not None
                min_kv_idx = torch.clamp(
                    logical_q_idx - (self.sliding_window - 1), min=0
                )
                min_block_idx = min_kv_idx // self.block_size
                sliding_mask = self.logical_block_ids >= min_block_idx[:, None]
                used_pages.masked_fill_(~sliding_mask, 0)
            if custom_hint:
                assert self.block_sparsity_hint is not None
                q_block_idx = logical_q_idx // self.block_size
                hint_mask = self.block_sparsity_hint.hint_fn(
                    q_block_idx[:, None],
                    self.logical_block_ids[None, :],
                    self.block_size,
                )
                used_pages.masked_fill_(~hint_mask, 0)

        used_pages_padded = pad_to_multiple(
            used_pages, multiple=self.q_block_size, dim=0
        )
        used_pages_padded = used_pages_padded.reshape(
            used_pages_padded.shape[0] // self.q_block_size, -1
        )
        used_pages_padded = used_pages_padded // page_to_block_ratio
        kv_indices = unique_static_unsorted(
            (used_pages_padded.long()), M=self.num_blocks
        ).to(torch.int32)
        kv_indices = copy_to_persistent(self.persistent_kv_indices, kv_indices)

        kv_num_blocks = (kv_indices >= 0).sum(dim=-1).to(torch.int32)
        kv_num_blocks = copy_to_persistent(self.persistent_kv_num_blocks, kv_num_blocks)

        block_mask_kwargs = {
            "seq_lengths": (self.num_actual_tokens, self.total_cache_tokens),
            "kv_num_blocks": kv_num_blocks[None, None],
            "kv_indices": kv_indices[None, None],
            "full_kv_num_blocks": None,
            "full_kv_indices": None,
            "BLOCK_SIZE": (self.q_block_size, self.kv_block_size),
            "mask_mod": self.mask_mod,
        }

        # compute_q_blocks parameter is available in PyTorch 2.9+
        if is_torch_equal_or_newer("2.9.0.dev0"):
            block_mask_kwargs["compute_q_blocks"] = False
        return BlockMask.from_kv_blocks(**block_mask_kwargs)