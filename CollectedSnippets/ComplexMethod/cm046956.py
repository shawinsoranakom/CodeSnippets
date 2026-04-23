def FalconH1Attention_fast_forward(
    self,
    hidden_states: torch.Tensor,
    causal_mask: Optional[BlockDiagonalCausalMask] = None,
    attention_mask: Optional[torch.Tensor] = None,
    position_ids: Optional[torch.LongTensor] = None,
    past_key_value: Optional[Tuple[torch.Tensor]] = None,
    output_attentions: bool = False,
    use_cache: bool = False,
    padding_mask: Optional[torch.LongTensor] = None,
    position_embeddings: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
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
    Q = Q.view(bsz, q_len, n_heads, head_dim)
    K = K.view(bsz, q_len, n_kv_heads, head_dim)
    V = V.view(bsz, q_len, n_kv_heads, head_dim).transpose(1, 2)
    seq_info = get_packed_info_from_kwargs(kwargs, hidden_states.device)

    # Falcon H1 multiplies key states by a multiplier
    K = K * self.config.key_multiplier

    Q = Q.transpose(1, 2)
    K = K.transpose(1, 2)

    kv_seq_len = K.shape[-2]
    if past_key_value is not None:
        kv_seq_len += past_key_value[0].shape[-2]

    # Extend RoPE dynamically to fit in VRAM
    if position_embeddings and kv_seq_len <= position_embeddings[0].shape[0]:
        cos, sin = position_embeddings
    else:
        rotary_emb = self.rotary_emb
        rotary_emb.extend_rope_embedding(V, seq_len = kv_seq_len)
        cos, sin = rotary_emb.get_cached(kv_seq_len, Q.device.index)

    rope_position_ids = (
        position_ids if position_ids is not None else kwargs.get("position_ids")
    )
    # Useful for LongRoPE
    Q, K = fast_rope_embedding(Q, K, cos, sin, rope_position_ids)

    if past_key_value is not None:
        K = torch.cat([past_key_value[0], K], dim = 2)
        V = torch.cat([past_key_value[1], V], dim = 2)
    past_key_value = (K, V) if use_cache else None

    # Attention module
    window = (-1, -1)
    use_varlen = (
        attention_mask is None
        and seq_info is not None
        and past_key_value is None
        and window == (-1, -1)
    )

    backend = (
        SDPA if attention_mask is not None else select_attention_backend(use_varlen)
    )
    attention_config = AttentionConfig(
        backend = backend,
        n_kv_heads = n_kv_heads,
        n_groups = n_groups,
        flash_dense_kwargs = {
            "causal": True,
            "window_size": (kv_seq_len, kv_seq_len),
        },
        flash_varlen_kwargs = {
            "dropout_p": 0.0,
            "softmax_scale": None,
            "causal": True,
        },
        sdpa_kwargs = {} if attention_mask is None else {"attn_mask": attention_mask},
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
    )

    A = run_attention(config = attention_config, context = context, Q = Q, K = K, V = V)

    attn_output = A.reshape(bsz, q_len, n_heads * head_dim)
    attn_output = self.apply_o(self, attn_output)
    attn_weights = None
    return attn_output, attn_weights, past_key_value