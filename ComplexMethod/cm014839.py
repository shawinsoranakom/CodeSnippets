def test_mem_efficient_attention_attn_mask_vs_math_ref_grads(self, device, batch_size: int, seq_len_q: int,
                                                                 seq_len_k: int, head_dim: int, is_causal: bool,
                                                                 dropout_p: float, dtype: torch.dtype,
                                                                 scale: str):
        def _get_mem_eff_drop_mask(batch_size, n_heads, q_len, kv_len, p, seed, offset, device=device):
            mask = torch.empty((batch_size, n_heads, q_len, kv_len), device=device, dtype=torch.float32)
            rand_uniform = torch._fill_mem_eff_dropout_mask_(mask, p, seed, offset)
            # On ROCM _fill_mem_eff_dropout_mask fills 0.5 if (prng > p) otherwise -0.5 to the tensor
            tester_p = p if not TEST_WITH_ROCM else 0.0
            mask = (rand_uniform > tester_p).to(torch.float32)
            return mask
        if max(seq_len_q, seq_len_k) >= 2048 and torch.cuda.get_device_properties('cuda').total_memory < 40 * 2**30:
            unittest.skip("Reference implementation OOM")
            return
        if TEST_WITH_ROCM and seq_len_q * seq_len_k * head_dim * batch_size > 1024 * 1024 * 128:
            torch.cuda.empty_cache()  # Prevent memory fragmentation
        seed = 42
        scale = scale if scale is None else (1 / head_dim)
        n_heads = 4
        query = torch.rand(batch_size, n_heads, seq_len_q, head_dim,
                           device=device, dtype=dtype, requires_grad=True)
        key = torch.rand(batch_size, n_heads, seq_len_k, head_dim, device=device,
                         dtype=dtype, requires_grad=True)
        value = torch.rand(batch_size, n_heads, seq_len_k, head_dim,
                           device=device, dtype=dtype, requires_grad=True)

        attn_mask = torch.rand(seq_len_q, seq_len_k, device=device, dtype=dtype, requires_grad=True)

        higher_precision_dtype = torch.float64 if dtype == torch.float32 else torch.float32
        query_ref, key_ref, value_ref = query_key_value_clones(query, key, value, dtype=higher_precision_dtype)
        attn_mask_ref = attn_mask.detach().to(higher_precision_dtype).requires_grad_(True)

        # Create real output
        with sdpa_kernel(backends=[SDPBackend.EFFICIENT_ATTENTION]):
            # Set the seed and run the kernel
            torch.manual_seed(seed)
            out = F.scaled_dot_product_attention(query, key, value, attn_mask, dropout_p=dropout_p,
                                                 is_causal=is_causal, scale=scale)

        if dropout_p == 0.0:
            with sdpa_kernel(backends=[SDPBackend.MATH]):
                # High Precision Math Reference
                out_ref = F.scaled_dot_product_attention(query_ref, key_ref, value_ref, attn_mask_ref,
                                                         dropout_p=dropout_p, is_causal=is_causal, scale=scale)
                # Low Precision Math Reference
                out_lp_ref = F.scaled_dot_product_attention(query, key, value, attn_mask,
                                                            dropout_p=dropout_p, is_causal=is_causal, scale=scale)
        else:
            if seq_len_q > 1024:
                self.skipTest("Will call _fill_mem_eff_dropout_mask with too many threads!")
            # Create the dropout_mask
            torch.manual_seed(seed)
            dropout_mask = _get_mem_eff_drop_mask(batch_size, n_heads, seq_len_q,
                                                  seq_len_k, dropout_p, seed, 0, device=device)
            # High Precision Math Reference
            out_ref = torch.ops.aten._scaled_dot_product_attention_math(
                query_ref, key_ref, value_ref, attn_mask_ref, dropout_p=dropout_p, is_causal=is_causal,
                scale=scale, dropout_mask=dropout_mask)[0]
            # Low Precision Math Reference
            out_lp_ref = torch.ops.aten._scaled_dot_product_attention_math(
                query, key, value, attn_mask,
                dropout_p=dropout_p, is_causal=is_causal, scale=scale,
                dropout_mask=dropout_mask)[0]

        upstream_grad = torch.rand_like(out, requires_grad=False)

        grads = torch.autograd.grad(out, (query, key, value, attn_mask), upstream_grad)
        grads_ref_lp = torch.autograd.grad(out_lp_ref, (query, key, value, attn_mask), upstream_grad)
        grads_ref = torch.autograd.grad(out_ref, (query_ref, key_ref, value_ref, attn_mask_ref), upstream_grad)

        fudge_factors = {
            "out": 4,
            "grad_query": 160.0,
            "grad_key": 25.0,
            "grad_value": 8.0,
            "grad_attn_mask": 45.0,
        }
        if TEST_WITH_ROCM:
            fudge_factors['out'] = 6.0
            fudge_factors['grad_key'] = 45.0
            fudge_factors['grad_query'] = 360.0
            if seq_len_k >= 1024:
                fudge_factors['grad_key'] = 70.0
            if seq_len_k >= 2048:
                fudge_factors['grad_key'] = 160.0
                fudge_factors['grad_query'] = 670.0  # gfx90a
            if dtype == torch.float32:
                fudge_factors['grad_key'] = 90.0
                if "gfx95" in torch.cuda.get_device_properties(0).gcnArchName:
                    fudge_factors['grad_value'] = 16.0

        check_out_and_grad(
            (out_ref, out_lp_ref, out),
            *zip(grads_ref, grads_ref_lp, grads),
            fudge_factors=fudge_factors,
        )