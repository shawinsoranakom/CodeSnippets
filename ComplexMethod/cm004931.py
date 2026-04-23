def _attend(
        self,
        query_vectors,
        key_vectors,
        value_vectors,
        sorted_bucket_idx_per_hash,
        attention_mask,
        do_standard_self_attention,
        use_cache,
    ):
        # look at previous and following chunks if chunked attention
        if not do_standard_self_attention:
            key_vectors = self._look_adjacent(key_vectors, self.num_chunks_before, self.num_chunks_after)
            value_vectors = self._look_adjacent(value_vectors, self.num_chunks_before, self.num_chunks_after)

        # get logits and dots
        # (BS, NumAttn, NumHash x NumChunk, Chunk_L x Hidden),(BS, NumAttn, NumHash x NumChunk, Chunk_L * (Num_bef + Num_aft + 1) x Hidden) -> (BS, NumAttn, NumHash x NumChunk, Chunk_L, Chunk_L * (1 + Num_bef + Num_aft))
        query_key_dots = torch.matmul(query_vectors, key_vectors.transpose(-1, -2))

        # free memory
        del query_vectors, key_vectors

        # if chunked attention split bucket idxs to query and key
        if not do_standard_self_attention:
            query_bucket_idx = self._split_seq_length_dim_to(
                sorted_bucket_idx_per_hash, -1, self.chunk_length, self.num_attention_heads
            )
            key_value_bucket_idx = self._look_adjacent(query_bucket_idx, self.num_chunks_before, self.num_chunks_after)
        elif use_cache and query_key_dots.ndim > 4:
            key_value_bucket_idx = sorted_bucket_idx_per_hash
            query_bucket_idx = (
                key_value_bucket_idx.new_ones(key_value_bucket_idx.shape[:-1] + (1,)) * key_value_bucket_idx.max()
            )
        elif use_cache and query_key_dots.ndim <= 4:
            query_bucket_idx = (query_key_dots.shape[-1] - 1) * torch.ones_like(query_key_dots)[:, :, :, -1]
            key_value_bucket_idx = torch.arange(
                query_key_dots.shape[-1], dtype=torch.long, device=query_key_dots.device
            )[None, None, :].expand(query_bucket_idx.shape[:2] + (-1,))
        else:
            query_bucket_idx = key_value_bucket_idx = sorted_bucket_idx_per_hash

        # get correct mask values depending on precision
        if query_key_dots.dtype == torch.float16:
            self_mask_value = self.self_mask_value_float16.half()
            mask_value = self.mask_value_float16.half()
        else:
            self_mask_value = self.self_mask_value_float32
            mask_value = self.mask_value_float32

        if not use_cache:
            mask = self._compute_attn_mask(
                query_bucket_idx,
                key_value_bucket_idx,
                attention_mask,
                query_key_dots.shape,
                do_standard_self_attention,
            )

            if mask is not None:
                query_key_dots = torch.where(mask, query_key_dots, mask_value)

            # free memory
            del mask

        # Self mask is ALWAYS applied.
        # From the reformer paper (https://huggingface.co/papers/2001.04451):
        # " While attention to the future is not allowed, typical implementations of the
        # Transformer do allow a position to attend to itself.
        # Such behavior is undesirable in a shared-QK formulation because the dot-product
        # of a query vector with itself will almost always be greater than the dot product of a
        # query vector with a vector at another position. We therefore modify the masking
        # to forbid a token from attending to itself, except in situations
        # where a token has no other valid attention targets (e.g. the first token in a sequence) "

        self_mask = torch.ne(query_bucket_idx.unsqueeze(-1), key_value_bucket_idx.unsqueeze(-2)).to(
            query_bucket_idx.device
        )

        # apply self_mask
        query_key_dots = torch.where(self_mask, query_key_dots, self_mask_value)

        # free memory
        del self_mask

        logits = torch.logsumexp(query_key_dots, dim=-1, keepdim=True)
        # dots shape is `[batch_size, num_attn_heads, num_hashes * seq_len // chunk_length, chunk_length, chunk_length * (1 + num_chunks_before + num_chunks_after)]`
        attention_probs = torch.exp(query_key_dots - logits)

        # free memory
        del query_key_dots

        # dropout
        attention_probs = nn.functional.dropout(attention_probs, p=self.dropout, training=self.training)

        # attend values
        out_vectors = torch.matmul(attention_probs, value_vectors)

        # free memory
        del value_vectors

        # merge chunk length
        if out_vectors.ndim > 4:
            logits = logits.flatten(start_dim=2, end_dim=3).squeeze(-1)
            out_vectors = out_vectors.flatten(start_dim=2, end_dim=3)

        return out_vectors, logits, attention_probs