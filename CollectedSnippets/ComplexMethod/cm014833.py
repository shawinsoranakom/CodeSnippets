def test_scaled_dot_product_fused_attention_gqa_vs_math_cpu(
        self,
        device,
        fused_kernel,
        dtype,
        n_heads,
        train,
    ):
        tol = Tolerances(1e-5, 5e-6)
        if dtype is torch.bfloat16:
            tol = Tolerances(5e-2, 5e-2)
        if dtype is torch.float16:
            tol = Tolerances(1e-2, 1e-2)
        tol_grad = Tolerances(1e-5, 5e-6)
        if dtype is torch.bfloat16:
            tol_grad = Tolerances(1e-1, 1e-1)
        if dtype is torch.float16:
            tol_grad = Tolerances(1e-1, 1e-1)
        q_n_head, kv_n_head = n_heads
        batch_size, q_seq_len, kv_seq_len, head_dim = 12, 17, 100, 8

        q, k, v = self._generate_fixed_qkv_helper(
            device, dtype, batch_size, q_n_head, kv_n_head, q_seq_len, kv_seq_len, head_dim)
        q2, k2, v2 = self._generate_fixed_qkv_helper(
            device, dtype, batch_size, q_n_head, kv_n_head, q_seq_len, kv_seq_len, head_dim)
        if train:
            q.requires_grad_(True)
            k.requires_grad_(True)
            v.requires_grad_(True)
            q2.requires_grad_(True)
            k2.requires_grad_(True)
            v2.requires_grad_(True)

        mask_shape = [batch_size, q_n_head, q_seq_len, kv_seq_len]
        attn_mask = torch.randn(mask_shape, dtype=dtype, device=device)

        with sdpa_kernel(backends=[fused_kernel]):
            actual = torch.nn.functional.scaled_dot_product_attention(
                q, k, v, attn_mask=attn_mask, dropout_p=0.0, enable_gqa=True)
        with sdpa_kernel(backends=[SDPBackend.MATH]):
            math_ref = torch.nn.functional.scaled_dot_product_attention(
                q2, k2, v2, attn_mask=attn_mask, dropout_p=0.0, enable_gqa=True)

        if dtype in [torch.bfloat16, torch.float16]:
            math_ref = math_ref.to(dtype)

        self.assertEqual(actual, math_ref, atol=tol.atol, rtol=tol.rtol)

        if train:
            actual.sum().backward()
            math_ref.sum().backward()

            grad_q_actual, grad_k_actual, grad_v_actual = q.grad, k.grad, v.grad
            grad_q_ref, grad_k_ref, grad_v_ref = q2.grad, k2.grad, v2.grad

            self.assertFalse(grad_q_actual is None)
            self.assertFalse(grad_k_actual is None)
            self.assertFalse(grad_v_actual is None)
            self.assertEqual(grad_q_actual, grad_q_ref, atol=tol_grad.atol, rtol=tol_grad.rtol)
            self.assertEqual(grad_k_actual, grad_k_ref, atol=tol_grad.atol, rtol=tol_grad.rtol)
            self.assertEqual(grad_v_actual, grad_v_ref, atol=tol_grad.atol, rtol=tol_grad.rtol)