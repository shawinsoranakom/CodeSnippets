def test_scaled_dot_product_fused_attention_mask_vs_math_cpu(
        self,
        device,
        fused_kernel,
        dtype,
        batch_size,
        q_seq_len,
        kv_seq_len,
        n_head,
        head_dim,
        mask_dim,
        bool_mask,
        train,
        casual,
        set_attn_mask,
    ):
        tol = Tolerances(1e-5, 5e-6)
        if dtype is torch.bfloat16:
            tol = Tolerances(5e-2, 5e-2)
        if dtype is torch.float16:
            tol = Tolerances(1e-2, 1e-2)
        tol_grad = Tolerances(1e-5, 5e-6)
        if dtype is torch.bfloat16:
            tol_grad = Tolerances(5e-2, 5e-2)
        if dtype is torch.float16:
            tol_grad = Tolerances(1e-1, 1e-1)
        if dtype is torch.float32:
            tol_grad = Tolerances(1.25e-5, 5.25e-6)
        for mask_shape in itertools.product(
            [q_seq_len, 1], [kv_seq_len, 1]
        ) if mask_dim == 2 else itertools.product(
            [batch_size, 1], [n_head, 1], [q_seq_len, 1], [kv_seq_len, 1]
        ):
            q, k, v = self._generate_fixed_qkv_helper(
                device, dtype, batch_size, n_head, n_head, q_seq_len, kv_seq_len, head_dim)
            q2, k2, v2 = self._generate_fixed_qkv_helper(
                device, dtype, batch_size, n_head, n_head, q_seq_len, kv_seq_len, head_dim)
            if train:
                q.requires_grad_(True)
                k.requires_grad_(True)
                v.requires_grad_(True)
                q2.requires_grad_(True)
                k2.requires_grad_(True)
                v2.requires_grad_(True)

            if set_attn_mask and not casual:
                if bool_mask:
                    attn_mask = torch.randint(0, 2, size=mask_shape, dtype=torch.bool, device=device)
                else:
                    attn_mask = torch.randn(mask_shape, dtype=dtype, device=device)
            else:
                attn_mask = None

            with sdpa_kernel(backends=[fused_kernel]):
                actual = torch.nn.functional.scaled_dot_product_attention(
                    q, k, v, attn_mask=attn_mask, dropout_p=0.0, is_causal=casual)
            with sdpa_kernel(backends=[SDPBackend.MATH]):
                math_ref = torch.nn.functional.scaled_dot_product_attention(
                    q2, k2, v2, attn_mask=attn_mask, dropout_p=0.0, is_causal=casual)

            if dtype in [torch.bfloat16, torch.float16]:
                math_ref = math_ref.to(dtype)

            self.assertFalse(torch.isnan(math_ref).any())
            self.assertFalse(torch.isnan(actual).any())

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