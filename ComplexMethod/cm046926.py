def Gemma2Attention_fast_forward_inference(
    self,
    hidden_states: torch.Tensor,
    past_key_value: Optional[Tuple[torch.Tensor]],
    position_ids,
    do_prefill = False,
    attention_mask = None,
    use_sliding_window = False,
    **kwargs,
):
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
        # Only for Gemma2
        self.temp_O = torch.empty((bsz, 1, hidden_size), dtype = dtype, device = device)
        self.attention = torch.empty(
            (bsz, n_heads, 1, KV_CACHE_INCREMENT + seq_len), dtype = dtype, device = device
        )

        # See https://github.com/google/gemma_pytorch/commit/03e657582d17cb5a8617ebf333c1c16f3694670e
        # Gemma 9b should use 256 and not 224 (hs / nah). 27b uses the below
        # We default to using the config file itself
        # s = self.config.hidden_size // self.config.num_attention_heads
        self.scalar = 1.0 / math_sqrt(self.config.query_pre_attn_scalar)
        # self.scalar = 1.0 / math_sqrt(self.config.hidden_size // self.config.num_attention_heads)
        self.half_head_dim = head_dim // 2
        self.t = self.config.attn_logit_softcapping
        self.reciprocal_t = 1.0 / self.config.attn_logit_softcapping
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

    # Handle sliding windows
    sliding_window = self.config.sliding_window
    if use_sliding_window and kv_seq_len > sliding_window:
        start = kv_seq_len - sliding_window
        Knn = Kn[:, :, start:, :]  # .contiguous()
        Vnn = Vn[:, :, start:, :]  # .contiguous()
    else:
        Knn, Vnn = Kn, Vn

    # Grouped query attention
    _, _, cached_len, _ = Knn.shape
    if n_groups != 1:
        Knn = Knn[:, :, None, :, :].expand(
            bsz, n_kv_heads, n_groups, cached_len, head_dim
        )
        Vnn = Vnn[:, :, None, :, :].expand(
            bsz, n_kv_heads, n_groups, cached_len, head_dim
        )
        Knn = Knn.reshape(bsz, n_heads, cached_len, head_dim)
        Vnn = Vnn.reshape(bsz, n_heads, cached_len, head_dim)

    # Attention
    # [TODO] Gemma2 uses manual matmul for all batch sizes because SDPA does
    # not support softcapping (tanh logit scaling). If a future PyTorch adds
    # a softcap param to scaled_dot_product_attention, consider using SDPA
    # for bsz > 1 to match the llama/qwen3 pattern.
    Qn *= (
        self.scalar
    )  # See https://github.com/ggerganov/llama.cpp/issues/7805#issuecomment-2153349963
    # It seems like doing (Q * scalar) @ K is better than (Q @ K) * scalar to stop overflows
    A = torch_matmul(Qn, Knn.transpose(2, 3), out = self.attention[:, :, :, :cached_len])

    # Softcapping must happen BEFORE the mask is applied.
    # Reference: google-deepmind/gemma _modules.py and transformers gemma2 eager_attention_forward
    A *= self.reciprocal_t
    A.tanh_()
    A *= self.t  # Logit softcapping

    if attention_mask is not None and isinstance(attention_mask, torch.Tensor):
        # Slice mask to match K/V when sliding window is active
        if attention_mask.shape[-1] != A.shape[-1]:
            attention_mask = attention_mask[:, :, :, -A.shape[-1] :]
        A += attention_mask

    A[:] = torch_nn_functional_softmax(A, dim = -1, dtype = torch.float32)  # .to(A.dtype)
    A = torch_matmul(A, Vnn, out = Qn)
    A = A.transpose(1, 2)
    A = A.reshape(bsz, 1, attention_size)
    A = fast_linear_forward(self.o_proj, A, out = self.temp_O)
    return A, (Kn, Vn)