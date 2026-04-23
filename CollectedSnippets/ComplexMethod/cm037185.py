def forward(
        self,
        layer: torch.nn.Module,
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        kv_cache: torch.Tensor,
        attn_metadata: FlexAttentionMetadata,
        output: torch.Tensor,
        output_scale: torch.Tensor | None = None,
        output_block_scale: torch.Tensor | None = None,
    ) -> torch.Tensor:
        """Forward pass with FLexAttention.

        Args:
            query: shape = [num_tokens, num_heads, head_size]
            key: shape = [num_tokens, num_kv_heads, head_size]
            value: shape = [num_tokens, num_kv_heads, head_size]
            kv_cache: shape =
                [2, num_blocks, block_size, num_kv_heads, head_size]
            attn_metadata: Metadata for attention.
        Returns:
            shape = [num_tokens, num_heads * head_size]
        """
        if output_scale is not None or output_block_scale is not None:
            raise NotImplementedError(
                "fused output quantization is not yet supported for FlexAttentionImpl"
            )

        enable_gqa = self.num_kv_heads != self.num_heads

        if attn_metadata is None:
            # Profiling run.
            return output.fill_(0)
            # query = self.view_as_4d(query).permute(0, 2, 1, 3)
            # return torch.empty_like(query)

        num_actual_tokens = attn_metadata.num_actual_tokens

        needs_rebuild_block_mask = False
        if attn_metadata.sliding_window != self.sliding_window:
            attn_metadata.sliding_window = self.sliding_window
            if attn_metadata.direct_build:
                # update mask mod in attention metadata
                attn_metadata.mask_mod = attn_metadata.get_mask_mod()
            needs_rebuild_block_mask = True

        if self.mm_prefix_range != getattr(attn_metadata, "mm_prefix_range", None):
            self.mm_prefix_range = attn_metadata.mm_prefix_range
            attn_metadata.mask_mod = attn_metadata.get_mask_mod()
            needs_rebuild_block_mask = True

        layer_mask_mod = getattr(layer, "logical_mask_mod", None)
        if (
            layer_mask_mod is not None
            and attn_metadata.logical_mask_mod is not layer_mask_mod
        ):
            attn_metadata.logical_mask_mod = layer_mask_mod
            attn_metadata.mask_mod = attn_metadata.get_mask_mod()
            needs_rebuild_block_mask = True

        layer_hint = getattr(layer, "block_sparsity_hint", None)
        if (
            layer_hint is not None
            and attn_metadata.block_sparsity_hint is not layer_hint
        ):
            attn_metadata.block_sparsity_hint = layer_hint
            needs_rebuild_block_mask = True

        if needs_rebuild_block_mask or attn_metadata.block_mask is None:
            if attn_metadata.direct_build:
                attn_metadata.block_mask = attn_metadata._build_block_mask_direct()
            else:
                attn_metadata.block_mask = attn_metadata.build_block_mask()

        if self.attn_type == AttentionType.ENCODER_ONLY:
            query, key_tensor, value_tensor = map(
                lambda x: self.view_as_4d(x).permute(0, 2, 1, 3),
                (query, key, value),
            )

            query = query[:, :, :num_actual_tokens, :]
            if (key_tensor.size(-2) > num_actual_tokens) or (
                value_tensor.size(-2) > num_actual_tokens
            ):
                # In the encoder-only model with torch.compile,
                # qkv might be padded, which might cause exception.
                # see: https://github.com/vllm-project/vllm/pull/24872#discussion_r2353252290
                key_tensor = key_tensor[:, :, :num_actual_tokens, :]
                value_tensor = value_tensor[:, :, :num_actual_tokens, :]

        else:
            assert self.attn_type == AttentionType.DECODER
            key_cache, value_cache = kv_cache.unbind(0)

            # View out the block_size dim
            key_cache = key_cache.view(-1, self.num_kv_heads, self.head_size)
            value_cache = value_cache.view(-1, self.num_kv_heads, self.head_size)
            query, key_tensor, value_tensor = map(
                lambda x: self.view_as_4d(x).permute(0, 2, 1, 3),
                (query, key_cache, value_cache),
            )

            query = query[:, :, :num_actual_tokens, :]

        # Doesn't work for now -> constraint violation
        # torch._dynamo.try_mark_dynamic(query, 2)

        assert attn_metadata.block_mask is not None
        block_m, block_n = attn_metadata.block_mask.BLOCK_SIZE

        kernel_options = get_kernel_options(
            query, block_m, block_n, attn_metadata.direct_build
        )
        out = flex_attention_compiled(
            query,
            key_tensor,
            value_tensor,
            attn_metadata.transformed_score_mod,
            attn_metadata.block_mask,
            self.scale,
            enable_gqa=enable_gqa,
            kernel_options=kernel_options,
        )

        # Flex doesn't have an out variant today, rely on epilogue fusion
        out = out.permute(0, 2, 1, 3).squeeze(0)
        output[:num_actual_tokens, :, :].copy_(out)
        return output