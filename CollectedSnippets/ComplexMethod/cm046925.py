def Gemma2Attention_fast_forward(
    self,
    hidden_states: torch.Tensor,
    causal_mask: Optional[BlockDiagonalCausalMask] = None,
    attention_mask: Optional[torch.Tensor] = None,
    position_ids: Optional[torch.LongTensor] = None,
    past_key_value: Optional[Tuple[torch.Tensor]] = None,
    output_attentions: bool = False,
    use_cache: bool = False,
    padding_mask: Optional[torch.LongTensor] = None,
    *args,
    **kwargs,
) -> Tuple[torch.Tensor, Optional[torch.Tensor], Optional[Tuple[torch.Tensor]]]:
    # Clear inference
    if hasattr(self, "paged_attention"):
        del self.paged_attention_K
        del self.paged_attention_V
        del self.paged_attention
        del self.temp_QA
        del self.temp_KV
        del self.RH_Q
        del self.attention

    bsz, q_len, _ = hidden_states.size()

    n_heads = self.config.num_attention_heads
    n_groups = self.num_key_value_groups
    n_kv_heads = self.config.num_key_value_heads
    head_dim = self.head_dim
    assert n_kv_heads * n_groups == n_heads

    Q, K, V = self.apply_qkv(self, hidden_states)
    Q = Q.view(bsz, q_len, n_heads, head_dim).transpose(1, 2)
    K = K.view(bsz, q_len, n_kv_heads, head_dim).transpose(1, 2)
    V = V.view(bsz, q_len, n_kv_heads, head_dim).transpose(1, 2)
    seq_info = get_packed_info_from_kwargs(kwargs, Q.device)

    kv_seq_len = K.shape[-2]
    if past_key_value is not None:
        kv_seq_len += past_key_value[0].shape[-2]

    device_index = Q.device.index
    cos = self.rotary_emb.multi_gpu_cos_cached[device_index]
    sin = self.rotary_emb.multi_gpu_sin_cached[device_index]

    rope_position_ids = (
        position_ids if position_ids is not None else kwargs.get("position_ids")
    )
    if rope_position_ids is not None:
        # Useful for LongRoPE
        cos_var, sin_var = self.rotary_emb.get_cached(kv_seq_len, device_index)
        Q, K = fast_rope_embedding(Q, K, cos_var, sin_var, rope_position_ids)
    else:
        Q, K = fast_rope_embedding(Q, K, cos, sin)

    if past_key_value is not None:
        K = torch.cat([past_key_value[0], K], dim = 2)
        V = torch.cat([past_key_value[1], V], dim = 2)
    past_key_value = (K, V) if use_cache else None

    # Only enable if the attention_mask is True
    use_sliding_window = kwargs.get("use_sliding_window")
    has_sliding_window = (
        use_sliding_window
        if use_sliding_window is not None
        else isinstance(causal_mask, bool) and causal_mask is True
    )

    use_flash = HAS_FLASH_ATTENTION_SOFTCAPPING and attention_mask is None

    if use_flash:
        window = (-1, -1)
        sliding_window = getattr(self.config, "sliding_window", None)
        if has_sliding_window:
            sliding_window = (
                sliding_window if sliding_window is not None else kv_seq_len
            )
            window = (
                (-1, -1)
                if kv_seq_len <= sliding_window
                else (sliding_window, sliding_window)
            )

        if not hasattr(self, "_flash_attention_softmax_scale"):
            self._flash_attention_softmax_scale = 1.0 / (
                self.config.query_pre_attn_scalar**0.5
            )

        use_varlen = seq_info is not None and past_key_value is None

        attention_config = AttentionConfig(
            backend = select_attention_backend(use_varlen),
            n_kv_heads = n_kv_heads,
            n_groups = n_groups,
            flash_dense_kwargs = {
                "causal": True,
                "softcap": self.config.attn_logit_softcapping,
                "softmax_scale": self._flash_attention_softmax_scale,
                "window_size": window,
            },
            flash_varlen_kwargs = {
                "dropout_p": 0.0,
                "softmax_scale": self._flash_attention_softmax_scale,
                "causal": True,
                "softcap": self.config.attn_logit_softcapping,
                "window_size": window,
            },
        )

        context = AttentionContext(
            bsz = bsz,
            q_len = q_len,
            kv_seq_len = kv_seq_len,
            n_heads = n_heads,
            head_dim = head_dim,
            requires_grad = hidden_states.requires_grad,
            seq_info = seq_info,
            attention_mask = attention_mask,
            causal_mask = causal_mask,
            sliding_window = sliding_window,
        )

        A = run_attention(config = attention_config, context = context, Q = Q, K = K, V = V)
        A = A.reshape(bsz, q_len, n_heads * head_dim)
    else:
        fx = (
            slow_inference_attention_softcapping
            if "_flag_for_generation" in kwargs
            else slow_attention_softcapping
        )
        A = fx(Q, K, V, causal_mask, self, bsz, kv_seq_len)
    A = self.apply_o(self, A)
    return A, None, past_key_value