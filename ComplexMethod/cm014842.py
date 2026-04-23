def test_fused_kernels_nested_broadcasting(
        self,
        device,
        kernel,
        expand_q_batch,
        expand_k_batch,
        expand_v_batch,
        expand_q_num_heads,
        expand_k_num_heads,
        expand_v_num_heads,
    ):
        is_efficient = kernel == SDPBackend.EFFICIENT_ATTENTION
        dtype = torch.float32 if is_efficient else torch.float16
        rand_nested_tensor = partial(rand_sdpa_tensor, type="nested", device=device, dtype=dtype)
        batch, num_heads, head_dim = 32, 8, 64
        head_dim_v = 32 if is_efficient else head_dim
        if TEST_WITH_ROCM and head_dim != head_dim_v:
            self.skipTest("head_dim != head_dim_v unsupported on ROCm for now")
            return
        seq_lens_q = (torch.randint(low=1, high=5, size=(1,)).item()
                      if expand_q_batch
                      else torch.randint(low=1, high=32, size=(batch,)).tolist())
        seq_lens_kv = (torch.randint(low=1, high=5, size=(1,)).item()
                       if (expand_k_batch or expand_v_batch)
                       else torch.randint(low=1, high=32, size=(batch,)).tolist())

        batch_q = 1 if expand_q_batch else batch
        batch_k = 1 if expand_k_batch else batch
        batch_v = 1 if expand_v_batch else batch

        # handle case where all batch_sizes are 1
        batch = max(batch_q, batch_k, batch_v)

        num_heads_q = 1 if expand_q_num_heads else num_heads
        num_heads_k = 1 if expand_k_num_heads else num_heads
        num_heads_v = 1 if expand_v_num_heads else num_heads

        # handle case where all num_heads are 1
        num_heads = max(num_heads_q, num_heads_k, num_heads_v)

        q_shape = SdpaShape(batch_q, num_heads_q, seq_lens_q, head_dim)
        k_shape = SdpaShape(batch_k, num_heads_k, seq_lens_kv, head_dim)
        v_shape = SdpaShape(batch_v, num_heads_v, seq_lens_kv, head_dim_v)

        query = rand_nested_tensor(q_shape)
        key = rand_nested_tensor(k_shape)
        value = rand_nested_tensor(v_shape)

        def _broadcast(t, batch_broadcasted, num_heads_broadcasted):
            if batch_broadcasted and num_heads_broadcasted:
                # (1, seq_len, 1, head_dim) -> (batch, seq_len, num_heads, head_dim)
                result = torch.nested.nested_tensor(
                    [t[0].expand(-1, num_heads, t.size(-1)) for _ in range(batch)], dtype=torch.float32)
            elif batch_broadcasted:
                # (1, seq_len, num_heads, head_dim) -> (batch, seq_len, num_heads, head_dim)
                result = torch.nested.nested_tensor([t[0] for _ in range(batch)], dtype=torch.float32)
            elif num_heads_broadcasted:
                # (batch, seq_len, 1, head_dim) -> (batch, seq_len, num_heads, head_dim)
                result = torch.nested.nested_tensor([x.expand(-1, num_heads, t.size(-1))
                                                    for x in t.unbind()], dtype=torch.float32)
            else:
                result = t.to(torch.float32)
            return result

        query_expanded = _broadcast(query, expand_q_batch, expand_q_num_heads).transpose(1, 2)
        key_expanded = _broadcast(key, expand_k_batch, expand_k_num_heads).transpose(1, 2)
        value_expanded = _broadcast(value, expand_v_batch, expand_v_num_heads).transpose(1, 2)

        query = query.transpose(1, 2)
        key = key.transpose(1, 2)
        value = value.transpose(1, 2)

        with sdpa_kernel(backends=[kernel]):
            actual = torch.nn.functional.scaled_dot_product_attention(
                query, key, value, attn_mask=None, dropout_p=0.0, is_causal=False)
        with sdpa_kernel(backends=[SDPBackend.MATH]):
            math_ref = torch.nn.functional.scaled_dot_product_attention(
                query_expanded.contiguous(), key_expanded.contiguous(), value_expanded.contiguous(),
                attn_mask=None, dropout_p=0.0, is_causal=False)

        self.assertEqual(actual.contiguous(), math_ref.contiguous().to(dtype), atol=1.5e-3, rtol=1e-2)