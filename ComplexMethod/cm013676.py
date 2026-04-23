def _dispatch(
        query: torch.Tensor,
        key: torch.Tensor,
        value: torch.Tensor,
        attn_mask: "CausalBias",
        dropout_p: float = 0.0,
        is_causal: bool = False,
        scale: float | None = None,
        enable_gqa: bool = False,
    ) -> torch.Tensor:
        r"""
        Handles the logic for computing attention with the specified causal bias.

        Args:
            query (Tensor): Query tensor; shape :math:`(N, ..., L, E)`.
            key (Tensor): Key tensor; shape :math:`(N, ..., S, E)`.
            value (Tensor): Value tensor; shape :math:`(N, ..., S, Ev)`.
            attn_mask (CausalBias): The type of causal attention to apply.
                A boolean mask where a value of True indicates that the element *should* take part in attention.
                A float mask of the same type as query, key, value that is added to the attention score.
            dropout_p (float): Dropout probability; if greater than 0.0, dropout is applied
            is_causal (bool): If true, assumes upper left causal attention masking and errors if both attn_mask and is_causal
                are set.
            scale (optional float): Scaling factor applied prior to softmax. If None, the default value is set
                to :math:`\frac{1}{\sqrt{E}}`.
            enable_gqa (optional bool): If set to True, Grouped Query Attention (GQA) is enabled, by default it is set to False.

        Returns:
            output (Tensor): Attention output; shape :math:`(N, ..., L, Ev)`.

        Raises:
            ValueError: If the causal bias variant is not a CausalVariant type.

        """
        if is_causal:
            raise ValueError("CausalBias should not be used with causal=True")

        if (
            attn_mask.seq_len_q == attn_mask.seq_len_kv
            or attn_mask.variant == CausalVariant.UPPER_LEFT
        ):
            return F.scaled_dot_product_attention(
                query,
                key,
                value,
                attn_mask=None,
                dropout_p=dropout_p,
                is_causal=True,
                scale=scale,
                enable_gqa=enable_gqa,
            )
        elif attn_mask.variant == CausalVariant.LOWER_RIGHT:
            _validate_sdpa_input(query, key, value, None, dropout_p, is_causal, scale)
            sdpa_params = SDPAParams(
                query, key, value, None, dropout_p, is_causal, enable_gqa
            )
            if can_use_flash_attention(sdpa_params):
                alignment = 64 if query.device.type == "xpu" else 8
                og_head_size = query.size(-1)
                og_scale = _calculate_scale(og_head_size, scale)
                needs_padding = og_head_size % alignment != 0
                if needs_padding:
                    pad_len = alignment - (og_head_size % alignment)
                    query = torch.nn.functional.pad(query, (0, pad_len))
                    key = torch.nn.functional.pad(key, (0, pad_len))
                    value = torch.nn.functional.pad(value, (0, pad_len))
                out = torch.ops.aten._scaled_dot_product_flash_attention(
                    query,
                    key,
                    value,
                    dropout_p,
                    is_causal=True,  # TODO: Flash accepts causal = True and for this particular op it means lower right
                    return_debug_mask=False,
                    scale=og_scale,
                )[0]
                return _postprocess_flash_output(out, og_head_size)
            if can_use_efficient_attention(sdpa_params):
                compute_log_sumexp = False
                if _input_requires_grad(query, key, value):
                    compute_log_sumexp = True
                return torch.ops.aten._efficient_attention_forward(
                    query.transpose(1, 2),
                    key.transpose(1, 2),
                    value.transpose(1, 2),
                    bias=None,
                    cu_seqlens_q=None,
                    cu_seqlens_k=None,
                    max_seqlen_q=None,
                    max_seqlen_k=None,
                    dropout_p=dropout_p,
                    custom_mask_type=int(attn_mask.variant),
                    compute_log_sumexp=compute_log_sumexp,
                    scale=scale,
                    seqlen_k=None,
                )[0].transpose(1, 2)
            else:
                _raise_kernel_warnings(sdpa_params)
                # We can't use efficient attention the only support for lower right is via materialization
                return F.scaled_dot_product_attention(
                    query,
                    key,
                    value,
                    attn_mask=attn_mask._materialize(query.device),
                    dropout_p=dropout_p,
                    is_causal=False,
                    scale=scale,
                    enable_gqa=enable_gqa,
                )
        else:
            raise ValueError(
                f"CausalBias.variant must be a CausalVariant type, but found: {attn_mask.variant}"
            )