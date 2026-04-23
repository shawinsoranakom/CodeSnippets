def GraniteAttention_fast_forward_inference(
    self,
    hidden_states: torch.Tensor,
    past_key_value: Optional[Tuple[torch.Tensor]],
    position_ids,
    do_prefill = False,
    attention_mask = None,
    use_sliding_window = False,
    position_embeddings: Optional[Tuple[torch.Tensor, torch.Tensor]] = None,
):
    assert (
        position_embeddings is not None
    ), f"Granite model requires position embeddings to be specified"

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
    device = hidden_states.device

    # Prefill phase
    # if not hasattr(self, "paged_attention"):
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
        self.temp_O = torch.empty((bsz, 1, hidden_size), dtype = dtype, device = device)
        self.attention = torch.empty(
            (bsz, n_heads, 1, KV_CACHE_INCREMENT + seq_len), dtype = dtype, device = device
        )

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
    Qn = Qn.view(bsz, 1, n_heads, head_dim).transpose(1, 2)
    Kn = Kn.view(bsz, 1, n_kv_heads, head_dim).transpose(1, 2)
    Vn = Vn.view(bsz, 1, n_kv_heads, head_dim).transpose(1, 2)

    # cos, sin = self.rotary_emb(Vn, seq_len = kv_seq_len)
    # Qn, Kn = inplace_rope_embedding(Qn, Kn, cos, sin, position_ids)
    cos, sin = position_embeddings
    # Transformers 5.x: position_ids may be [batch, full_seq_len]; slice to last
    if position_ids.dim() >= 2 and position_ids.shape[-1] > 1:
        position_ids = position_ids[:, -1:]
    cos, sin = cos[position_ids], sin[position_ids]
    h = self.half_head_dim

    RH_Q = self.RH_Q
    RH_Q[:, :, :, :h] = Qn[:, :, :, h:]
    RH_Q[:, :, :, h:] = Qn[:, :, :, :h]
    RH_Q[:, :, :, :h].neg_()
    Qn *= cos
    Qn.addcmul_(RH_Q, sin)

    RH_K = RH_Q[
        :, :n_kv_heads, :, :
    ]  # torch.empty((n_kv_heads, 1, head_dim), dtype = dtype, device = "cuda:0")
    RH_K[:, :, :, :h] = Kn[:, :, :, h:]
    RH_K[:, :, :, h:] = Kn[:, :, :, :h]
    RH_K[:, :, :, :h].neg_()
    Kn *= cos
    Kn.addcmul_(RH_K, sin)

    # New KV cache
    # Kn = torch.cat([K1, Kn], dim = 2)
    # Vn = torch.cat([V1, Vn], dim = 2)
    self.paged_attention_K[seq_len] = Kn.permute(2, 0, 1, 3)
    self.paged_attention_V[seq_len] = Vn.permute(2, 0, 1, 3)
    Kn = self.paged_attention_K[:kv_seq_len].permute(1, 2, 0, 3)
    Vn = self.paged_attention_V[:kv_seq_len].permute(1, 2, 0, 3)

    # Grouped query attention
    _, _, cached_len, _ = Kn.shape
    if bsz == 1 or ((not SDPA_HAS_GQA) and n_groups != 1):
        Kn = Kn[:, :, None, :, :].expand(
            bsz, n_kv_heads, n_groups, cached_len, head_dim
        )
        Vn = Vn[:, :, None, :, :].expand(
            bsz, n_kv_heads, n_groups, cached_len, head_dim
        )
        Kn = Kn.reshape(bsz, n_heads, cached_len, head_dim)
        Vn = Vn.reshape(bsz, n_heads, cached_len, head_dim)

    # Attention
    if bsz == 1:
        Qn *= self.scaling
        A = torch_matmul(
            Qn, Kn.transpose(2, 3), out = self.attention[:, :, :, :cached_len]
        )
        A[:] = torch_nn_functional_softmax(A, dim = -1, dtype = torch.float32)
        A = torch_matmul(A, Vn, out = Qn)
    else:
        if (
            attention_mask is not None
            and attention_mask.dim() == 4
            and attention_mask.dtype != torch.bool
        ):
            attention_mask = attention_mask.eq(0)
        if SDPA_HAS_GQA:
            A = scaled_dot_product_attention(
                Qn,
                Kn,
                Vn,
                attn_mask = attention_mask,
                scale = self.scaling,
                enable_gqa = True,
            )
        else:
            A = scaled_dot_product_attention(
                Qn,
                Kn,
                Vn,
                attn_mask = attention_mask,
                scale = self.scaling,
            )
    A = A.transpose(1, 2)
    A = A.reshape(bsz, 1, attention_size)
    A = fast_linear_forward(self.o_proj, A, out = self.temp_O)
    return A, (Kn, Vn)