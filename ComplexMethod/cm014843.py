def test_onednn_attention_mask_vs_math(
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
    ):
        # Migrate from TestSDPACpuOnly
        tol = Tolerances(1e-5, 5e-6)
        if dtype is torch.bfloat16:
            tol = Tolerances(5e-2, 5e-2)
        if dtype is torch.float16:
            tol = Tolerances(1e-2, 1e-2)
        mask_shape = [batch_size, 1, 1, kv_size]
        make_tensor = partial(rand_sdpa_tensor, type="dense", device=device, dtype=dtype, requires_grad=False)
        q_shape = SdpaShape(batch_size, n_head, q_size, head_dim)
        kv_shape = SdpaShape(batch_size, n_head, kv_size, head_dim)
        q = make_tensor(q_shape)
        k = make_tensor(kv_shape)
        v = make_tensor(kv_shape)
        q2, k2, v2 = q.clone(), k.clone(), v.clone()

        if train:
            q.requires_grad_(True)
            k.requires_grad_(True)
            v.requires_grad_(True)
            q2.requires_grad_(True)
            k2.requires_grad_(True)
            v2.requires_grad_(True)

        # (B, nh, T, hs)
        q = q.view(batch_size, q_size, n_head, head_dim).transpose(1, 2)
        k = k.view(batch_size, kv_size, n_head, head_dim).transpose(1, 2)
        v = v.view(batch_size, kv_size, n_head, head_dim).transpose(1, 2)
        attn_mask = None
        is_causal = False
        if mask_type == "bool":
            attn_mask = torch.randint(0, 2, size=mask_shape, dtype=torch.bool, device=device)
        elif mask_type == "float":
            attn_mask = torch.randn(mask_shape, dtype=dtype, device=device)
        elif mask_type == "causal":
            is_causal = True

        q2, k2, v2 = q2.float(), k2.float(), v2.float()
        q2 = q2.view(batch_size, q_size, n_head, head_dim).transpose(1, 2)
        k2 = k2.view(batch_size, kv_size, n_head, head_dim).transpose(1, 2)
        v2 = v2.view(batch_size, kv_size, n_head, head_dim).transpose(1, 2)
        attn_mask2 = attn_mask.float() if attn_mask is not None else None

        if fused_kernel == SDPBackend.MATH:
            actual = torch.ops.aten._scaled_dot_product_attention_math(
                q, k, v, attn_mask=attn_mask, dropout_p=0.0, is_causal=is_causal)[0]
        elif fused_kernel == SDPBackend.OVERRIDEABLE:
            actual = torch.ops.aten._scaled_dot_product_fused_attention_overrideable(
                q, k, v, attn_bias=attn_mask, dropout_p=0.0, is_causal=is_causal)[0]

        math_ref = torch.ops.aten._scaled_dot_product_attention_math(
            q2, k2, v2, attn_mask=attn_mask2, dropout_p=0.0, is_causal=is_causal)[0]

        self.assertEqual(actual.float(), math_ref, atol=tol.atol, rtol=tol.rtol)