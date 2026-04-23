def get_model_kwargs(self, use_padding: bool = False) -> dict[str, Any]:
        """Get model keyword arguments for the current batch, eventually padding the query dimension and KV dimensions
        if use_padding is True. The padding is only useful if we want static shapes, like when using cuda graphs."""
        q_size = self.num_q_tokens
        kv_size = self.max_kv_read + self.num_q_tokens
        batch_size = self.num_q_tokens if use_padding else self.true_batch_size

        # Prepare the kwargs, the attributes that are either tensors or dict of tensors are initialized to empty dicts.
        kwargs = PagedAttentionArgs(
            input_ids=self.input_ids[:q_size].unsqueeze(0),
            position_ids=self.position_ids[:q_size].unsqueeze(0),
            cu_seq_lens_q=self.cumulative_seqlens_q[: batch_size + 1],
            max_seqlen_q=self.max_seqlen_q,
            logits_indices=self.logits_indices[:q_size],
            logits_processor_args=self._bulk_input_tensor[self.static_inputs :, :q_size],
            cu_seq_lens_k={},
            max_seqlen_k={},
            attention_mask=None if self.attention_mask is None else {},
            read_index=[],
            write_index=[],
            cache=self.cache,
            block_table=self.block_table[:, :batch_size] if self.use_block_table else None,
            use_cache=False,
        )

        # If there is padding, make sure the padding sequences have length 0 (ie. cumulative lengths plateau)
        if use_padding:
            kwargs.cu_seq_lens_q[self.true_batch_size + 1 :] = self.total_seqlen_q
            # Additionally, if there are CUDA graphs, we need to pad max_seqlen so graph capture will work regardless of
            # the future Q / KV lengths of the next batches
            if not self.use_block_table and self.use_cuda_graph_varlen:
                self.max_seqlen_q = q_size
                self.max_seqlen_k = {
                    layer_type: pad_to_pow2(self.max_seqlen_k[layer_type], self.cache.num_pages, 1024)
                    for layer_type in self.max_seqlen_k.keys()
                }

        # When using block table, max_seqlen_q and max_seqlen_k are not used by flash_attn_with_kvcache, so we set them
        # to constant `1` to avoid dynamo guards on these changing integer values. This applies throughout this method.
        kwargs.max_seqlen_q = 1 if self.use_block_table else self.max_seqlen_q

        # For the attributes that are lists of tensors, we construct list of tensor references
        for i in range(self.cache.num_groups):
            read_index_size = kv_size if use_padding else self.true_read_sizes[i]
            write_index_size = q_size if use_padding else self.true_write_sizes[i]
            kwargs.read_index.append(self.read_index_storage[i, :read_index_size])
            kwargs.write_index.append(self.write_index_storage[i, :write_index_size])

        # For the attributes that are dict of tensors, we first fill the dict with the actual values
        for layer_type, seqlens_k in self.cumulative_seqlens_k.items():
            kwargs.cu_seq_lens_k[layer_type] = seqlens_k[: batch_size + 1]
            if use_padding:
                kwargs.cu_seq_lens_k[layer_type][self.true_batch_size + 1 :] = seqlens_k[self.true_batch_size]
            kwargs.max_seqlen_k[layer_type] = 1 if self.use_block_table else self.max_seqlen_k[layer_type]
            if self.attention_mask is not None:
                k_len = kv_size if use_padding else seqlens_k[batch_size]
                kwargs.attention_mask[layer_type] = self.attention_mask[layer_type][..., :q_size, :k_len]

        # If there is only one layer type, we remove the dicts around some attributes to avoid unnecessary overhead
        if len(self.cumulative_seqlens_k.keys()) == 1:
            kwargs.cu_seq_lens_k = kwargs.cu_seq_lens_k.popitem()[1]  # type: ignore
            kwargs.max_seqlen_k = kwargs.max_seqlen_k.popitem()[1]  # type: ignore
            if self.attention_mask is not None:
                kwargs.attention_mask = kwargs.attention_mask.popitem()[1]  # type: ignore

        return kwargs.asdict()