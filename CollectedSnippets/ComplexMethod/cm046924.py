def Qwen3Attention_fast_forward_inference(
    self,
    hidden_states: torch.Tensor,
    past_key_value: Optional[Tuple[torch.Tensor]],
    position_ids,
    do_prefill = False,
    attention_mask = None,
    **kwargs,
):
    """
    https://github.com/huggingface/transformers/blob/main/src/transformers/models/llama/modeling_llama.py#L406
    Fast inference using KV cache.
    QK^T can be computed in 4 chunks

    [Q, q] @ [K, k].T where q, k are the new tokens.
    [QK^T, Qk^T]
    [qK^T, qk^T]

    Since the attention mask wipes Qk^T, we just get
    [QK^T,    0]
    [qK^T, qk^T]

    Since softmax is row-wise, we get
    softmax([QK^T,    0])
    softmax([qK^T, qk^T])

    We then multiply by   [V]
                          [v]
    softmax([QK^T,    0]) [softmax(QK^T)V] *
    softmax([qK^T, qk^T]) [softmax([qK^T, qk^T]) @ [V, v]]

    But notice * [softmax(QK^T)V] is just the last attention.
    We just need to compute the last final row.

    This means we can pass in a row of Q, but we need to
    remember K and V, which are called the KV cache.
    """
    Xn = hidden_states
    bsz, _, hd = hidden_states.size()
    K1, V1 = past_key_value
    dtype = Xn.dtype

    n_heads = self.config.num_attention_heads
    n_groups = self.num_key_value_groups
    n_kv_heads = self.config.num_key_value_heads
    head_dim = self.head_dim
    # assert(n_kv_heads * n_groups == n_heads)

    hidden_size = self.config.hidden_size
    attention_size = n_heads * head_dim
    seq_len = K1.shape[-2]
    kv_seq_len = seq_len + 1

    # Prefill phase
    # if not hasattr(self, "paged_attention"):
    device = hidden_states.device
    if do_prefill:
        self.paged_attention = torch.empty(
            (KV_CACHE_INCREMENT + seq_len + 1, 2, bsz, n_kv_heads, head_dim),
            dtype = dtype,
            device = device,
        )
        self.paged_attention_K = self.paged_attention[:, 0]
        self.paged_attention_V = self.paged_attention[:, 1]
        self.paged_attention_K[:seq_len] = K1.permute(2, 0, 1, 3)
        self.paged_attention_V[:seq_len] = V1.permute(2, 0, 1, 3)
        self.temp_QA = torch.empty(
            (2, bsz, 1, attention_size), dtype = dtype, device = device
        )
        self.temp_KV = torch.empty(
            (2, bsz, 1, n_kv_heads * head_dim), dtype = dtype, device = device
        )
        self.RH_Q = torch.empty((bsz, n_heads, 1, head_dim), dtype = dtype, device = device)

        # Mistral Nemo 12b has weird dimensions
        if attention_size != hidden_size:
            self.temp_O = torch.empty((bsz, 1, hidden_size), dtype = dtype, device = device)
        else:
            self.temp_O = self.temp_QA[1][:, :, :hidden_size]

        self.attention = torch.empty(
            (bsz, n_heads, 1, KV_CACHE_INCREMENT + seq_len), dtype = dtype, device = device
        )
        self.scalar = 1.0 / math_sqrt(self.head_dim)
        self.half_head_dim = head_dim // 2
    elif kv_seq_len >= self.paged_attention.shape[0]:
        self.paged_attention.resize_(
            (
                self.paged_attention.shape[0] + KV_CACHE_INCREMENT,
                2,
                bsz,
                n_kv_heads,
                head_dim,
            )
        )
        self.paged_attention_K = self.paged_attention[:, 0]
        self.paged_attention_V = self.paged_attention[:, 1]
        self.attention.resize_(
            (bsz, n_heads, 1, self.attention.shape[-1] + KV_CACHE_INCREMENT)
        )

    Qn = fast_linear_forward(self.q_proj, Xn, out = self.temp_QA[0])
    Kn = fast_linear_forward(self.k_proj, Xn, out = self.temp_KV[0])
    Vn = fast_linear_forward(self.v_proj, Xn, out = self.temp_KV[1])
    Qn = Qn.view(
        bsz, 1, n_heads, head_dim
    )  # .transpose(1, 2) # we will transpose after normalisation
    Kn = Kn.view(
        bsz, 1, n_kv_heads, head_dim
    )  # .transpose(1, 2) # we will transpose after normalisation
    Vn = Vn.view(bsz, 1, n_kv_heads, head_dim).transpose(1, 2)

    Qn = fast_rms_layernorm_inference(self.q_norm, Qn)
    Kn = fast_rms_layernorm_inference(self.k_norm, Kn)

    Qn = Qn.transpose(1, 2)
    Kn = Kn.transpose(1, 2)

    # cos, sin = self.rotary_emb(Vn, seq_len = kv_seq_len)
    # Qn, Kn = inplace_rope_embedding(Qn, Kn, cos, sin, position_ids)

    # Need to do it prior 2 steps before hitting full on short KV cache
    # or else error
    self.rotary_emb.extend_rope_embedding(Vn, seq_len + 2)
    cos, sin = self.rotary_emb.get_cached(kv_seq_len, Qn.device.index)
    # Transformers 5.x: position_ids may be [batch, full_seq_len]; slice to last
    if position_ids.dim() >= 2 and position_ids.shape[-1] > 1:
        position_ids = position_ids[:, -1:]
    cos = cos[position_ids].unsqueeze(1)
    sin = sin[position_ids].unsqueeze(1)
    h = self.half_head_dim

    RH_Q = self.RH_Q
    RH_Q[:, :, :, :h] = Qn[:, :, :, h:]
    RH_Q[:, :, :, h:] = Qn[:, :, :, :h]
    RH_Q[:, :, :, :h].neg_()  # torch.neg(RH_Q[:,:,:,:h], out = RH_Q[:,:,:,:h])
    Qn *= cos
    Qn.addcmul_(RH_Q, sin)

    RH_K = RH_Q[
        :, :n_kv_heads, :, :
    ]  # torch.empty((n_kv_heads, 1, head_dim), dtype = dtype, device = "cuda:0")
    RH_K[:, :, :, :h] = Kn[:, :, :, h:]
    RH_K[:, :, :, h:] = Kn[:, :, :, :h]
    RH_K[:, :, :, :h].neg_()  # torch.neg(RH_K[:,:,:,:h], out = RH_K[:,:,:,:h])
    Kn *= cos
    Kn.addcmul_(RH_K, sin)

    # New KV cache
    # Kn = torch.cat([K1, Kn], dim = 2)
    # Vn = torch.cat([V1, Vn], dim = 2)
    self.paged_attention_K[seq_len] = Kn.permute(2, 0, 1, 3)
    self.paged_attention_V[seq_len] = Vn.permute(2, 0, 1, 3)
    Kn = self.paged_attention_K[:kv_seq_len].permute(1, 2, 0, 3)
    Vn = self.paged_attention_V[:kv_seq_len].permute(1, 2, 0, 3)

    # Handle sliding windows
    sliding_window = getattr(self.config, "sliding_window", None)
    if sliding_window is not None and kv_seq_len > sliding_window:
        start = kv_seq_len - sliding_window
        Knn = Kn[:, :, start:, :]  # .contiguous()
        Vnn = Vn[:, :, start:, :]  # .contiguous()
        if attention_mask is not None:
            attention_mask = attention_mask[..., start:]
    else:
        Knn, Vnn = Kn, Vn

    # when qlen==vlen and attn_mask is None, we should use causal attention
    Q_len = Qn.shape[-2]
    K_len = Knn.shape[-2]
    if attention_mask is not None and attention_mask.dim() == 2:
        attention_mask = attention_mask[:, None, None, :].to(torch.bool)
    elif (
        attention_mask is not None
        and attention_mask.dim() == 4
        and attention_mask.dtype != torch.bool
    ):
        attention_mask = attention_mask.eq(0)
    if attention_mask is None and Q_len == K_len:
        is_causal = True
    else:
        is_causal = False
    use_sdpa_gqa = SDPA_HAS_GQA
    if (
        use_sdpa_gqa
        and isinstance(attention_mask, torch.Tensor)
        and attention_mask.dim() >= 3
        and attention_mask.shape[0] > 1
    ):
        # Avoid SDPA GQA drift for batched masked decode.
        use_sdpa_gqa = False

    # Grouped query attention
    _, _, cached_len, _ = Knn.shape
    if bsz == 1 or ((not use_sdpa_gqa) and n_groups != 1):
        Knn = Knn[:, :, None, :, :].expand(
            bsz, n_kv_heads, n_groups, cached_len, head_dim
        )
        Vnn = Vnn[:, :, None, :, :].expand(
            bsz, n_kv_heads, n_groups, cached_len, head_dim
        )
        Knn = Knn.reshape(bsz, n_heads, cached_len, head_dim)
        Vnn = Vnn.reshape(bsz, n_heads, cached_len, head_dim)

    # Attention
    if bsz == 1:
        Qn *= self.scalar  # See https://github.com/ggerganov/llama.cpp/issues/7805#issuecomment-2153349963
        # It seems like doing (Q * scalar) @ K is better than (Q @ K) * scalar to stop overflows
        A = torch_matmul(
            Qn, Knn.transpose(2, 3), out = self.attention[:, :, :, :cached_len]
        )
        A[:] = torch_nn_functional_softmax(
            A, dim = -1, dtype = torch.float32
        )  # .to(A.dtype)
        A = torch_matmul(A, Vnn, out = Qn)
    else:
        if use_sdpa_gqa:
            A = scaled_dot_product_attention(
                Qn,
                Knn,
                Vnn,
                attn_mask = attention_mask,
                is_causal = is_causal,
                enable_gqa = True,
            )
        else:
            A = scaled_dot_product_attention(
                Qn, Knn, Vnn, attn_mask = attention_mask, is_causal = is_causal
            )
    A = A.transpose(1, 2)
    A = A.reshape(bsz, 1, attention_size)
    A = fast_linear_forward(self.o_proj, A, out = self.temp_O)
    return A, (Kn, Vn)