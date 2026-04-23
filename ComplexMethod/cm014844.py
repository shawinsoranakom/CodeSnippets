def test_flash_attention_vs_math(
        self,
        device,
        fused_kernel,
        dtype,
        batch_size,
        q_size,
        kv_size,
        n_head,
        head_dim,
        mask_type,
        train,
        layout,
        enable_gqa,
    ):
        if mask_type == "causal" and q_size != kv_size:
            self.skipTest("Flash Attention V2 does not accept is_causal when seq_len_q != seq_len_k")

        tol = Tolerances(1e-5, 5e-6)
        if dtype is torch.bfloat16:
            tol = Tolerances(5e-2, 5e-2)
        if dtype is torch.float16:
            tol = Tolerances(1e-2, 1e-2)
        make_tensor = partial(rand_sdpa_tensor, type="dense", device=device, dtype=dtype, requires_grad=False)

        if enable_gqa:
            n_head_q, n_head_kv = n_head[0], n_head[1]
        else:
            n_head_q = n_head_kv = n_head[0]

        q_shape = SdpaShape(batch_size, n_head_q, q_size, head_dim)
        kv_shape = SdpaShape(batch_size, n_head_kv, kv_size, head_dim)
        q = make_tensor(q_shape)
        k = make_tensor(kv_shape)
        v = make_tensor(kv_shape)

        # (B, S, H, D) by default
        q = q.view(batch_size, q_size, n_head_q, head_dim).transpose(1, 2)
        k = k.view(batch_size, kv_size, n_head_kv, head_dim).transpose(1, 2)
        v = v.view(batch_size, kv_size, n_head_kv, head_dim).transpose(1, 2)
        if layout == "bhsd":
            q = q.contiguous()
            k = k.contiguous()
            v = v.contiguous()

        is_causal = False
        if mask_type == "causal":
            is_causal = True

        q2, k2, v2 = q.clone(), k.clone(), v.clone()
        q2, k2, v2 = q2.float(), k2.float(), v2.float()

        if train:
            q = q.detach().clone().requires_grad_(True)
            k = k.detach().clone().requires_grad_(True)
            v = v.detach().clone().requires_grad_(True)
            q2 = q2.detach().clone().requires_grad_(True)
            k2 = k2.detach().clone().requires_grad_(True)
            v2 = v2.detach().clone().requires_grad_(True)

        with sdpa_kernel(backends=[fused_kernel]):
            actual = F.scaled_dot_product_attention(
                q, k, v, dropout_p=0.0, is_causal=is_causal, enable_gqa=enable_gqa)

        with sdpa_kernel(backends=[SDPBackend.MATH]):
            if is_causal:
                bottom_right_mask = causal_lower_right(q_size, kv_size)
                math_ref = F.scaled_dot_product_attention(
                    q2, k2, v2, dropout_p=0.0, attn_mask=bottom_right_mask, enable_gqa=enable_gqa)
            else:
                math_ref = F.scaled_dot_product_attention(
                    q2, k2, v2, dropout_p=0.0, is_causal=is_causal, enable_gqa=enable_gqa)

        if dtype in [torch.float16, torch.bfloat16]:
            math_ref = math_ref.to(dtype)

        self.assertEqual(actual, math_ref, atol=tol.atol, rtol=tol.rtol)

        if train:
            loss = torch.mean(actual)
            loss_ref = torch.mean(math_ref)
            loss.backward()
            loss_ref.backward()

            grad_q_actual, grad_k_actual, grad_v_actual = q.grad, k.grad, v.grad
            grad_q_ref, grad_k_ref, grad_v_ref = q2.grad, k2.grad, v2.grad
            if dtype in [torch.float16, torch.bfloat16]:
                grad_q_ref = grad_q_ref.to(dtype)
                grad_k_ref = grad_k_ref.to(dtype)
                grad_v_ref = grad_v_ref.to(dtype)

            self.assertEqual(grad_q_actual, grad_q_ref, atol=tol.atol, rtol=tol.rtol)
            self.assertEqual(grad_k_actual, grad_k_ref, atol=tol.atol, rtol=tol.rtol)
            self.assertEqual(grad_v_actual, grad_v_ref, atol=tol.atol, rtol=tol.rtol)