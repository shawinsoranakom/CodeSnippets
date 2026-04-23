def test_flash_attention_vs_math_ref_grads(self, device, batch_size: int, seq_len_q: int, seq_len_k: int,
                                               head_dim: int, is_causal: bool, dropout_p: float,
                                               dtype: torch.dtype, scale: str, enable_gqa: bool,
                                               n_heads: list[int], sdpa_backend: str):
        if isSM8XDevice or isSM120Device and head_dim in range(193, 256 + 1):
            self.skipTest("Flash attention on sm86, sm87, and sm89 for headdim > 192 currently disabled")
        if is_causal and seq_len_q != seq_len_k:
            self.skipTest("Flash V2 does not accept is_casual when seq_len_q != seq_len_k")
        if TEST_WITH_ROCM and seq_len_q >= 1024 and seq_len_k >= 1024 and batch_size > 1:
            torch.cuda.empty_cache()  # Prevent memory fragmentation
        if max(seq_len_q, seq_len_k) >= 2048 and torch.cuda.get_device_properties('cuda').total_memory < 40 * 2**30:
            unittest.skip("Reference implementation OOM")
            return

        # ROCm now supports 2 different backends for SDPA that require different set up.
        TEST_WITH_CK = False
        if TEST_WITH_ROCM:
            torch.backends.cuda.preferred_rocm_fa_library(sdpa_backend)
            # When no args are given to preferred_rocm_fa_library, it acts as a getter
            TEST_WITH_CK = (torch.backends.cuda.preferred_rocm_fa_library() == torch._C._ROCmFABackend.Ck)

        if TEST_WITH_CK and head_dim > 128:
            self.skipTest("CK does not support head dims over 128")

        base_condition = (
            TEST_WITH_ROCM and isRocmArchAnyOf(MI350_ARCH)
            and dtype == torch.float16 and scale is None and batch_size == 8
            and seq_len_q == 2048 and is_causal is False
        )

        # (seq_len_k, head_dim, enable_gqa) rows that should be skipped
        skip_cases = {
            (2048, 256, False),
            (2048, 203, False),
            (127, 256, False),
            (579, 256, True),
            (2048, 256, True),
        }

        if base_condition and (seq_len_k, head_dim, enable_gqa) in skip_cases:
            self.skipTest("Accuracy issues on gfx950")

        scale = scale if scale is None else (1 / head_dim)
        num_heads_q = num_heads_kv = 4
        if enable_gqa:
            num_heads_q = n_heads[0]
            num_heads_kv = n_heads[1]

        query = torch.rand(batch_size, num_heads_q, seq_len_q, head_dim,
                           device=device, dtype=dtype, requires_grad=True)
        key = torch.rand(batch_size, num_heads_kv, seq_len_k, head_dim, device=device,
                         dtype=dtype, requires_grad=True)
        value = torch.rand(batch_size, num_heads_kv, seq_len_k, head_dim,
                           device=device, dtype=dtype, requires_grad=True)

        higher_precision_dtype = torch.float64 if dtype == torch.float32 else torch.float32
        query_ref, key_ref, value_ref = query_key_value_clones(query, key, value, dtype=higher_precision_dtype)

        is_dropout = dropout_p > 0.0

        if not is_dropout:
            with sdpa_kernel(backends=[SDPBackend.FLASH_ATTENTION]):
                out = F.scaled_dot_product_attention(
                    query, key, value, dropout_p=dropout_p, is_causal=is_causal, scale=scale, enable_gqa=enable_gqa)
            with sdpa_kernel(backends=[SDPBackend.MATH]):
                # High Precision Math Reference
                out_ref = F.scaled_dot_product_attention(
                    query_ref, key_ref, value_ref, is_causal=is_causal, scale=scale, enable_gqa=enable_gqa)
                # Low Precision Math Reference
                out_lp_ref = F.scaled_dot_product_attention(
                    query, key, value, is_causal=is_causal, scale=scale, enable_gqa=enable_gqa)
        else:
            # Problem: We pad sizes in the composite region of the top level SDPA. But we need the
            # Debug mask when have dropout. So I am going to manually pad up here when testing dropout
            q_padded, q_og_size = pad_last_dim(query, 8)
            k_padded, k_og_size = pad_last_dim(key, 8)
            v_padded, v_og_size = pad_last_dim(value, 8)
            # scale needs to be calculated on the og head_size
            if scale is None:
                scale = 1 / math.sqrt(q_og_size)
            output_tuple = torch.ops.aten._scaled_dot_product_flash_attention(
                q_padded, k_padded, v_padded, dropout_p=dropout_p, is_causal=is_causal, scale=scale, return_debug_mask=is_dropout)
            out = output_tuple[0]
            out = out[..., :v_og_size]
            # Build dropout_mask
            dbug_mask = output_tuple[-1]
            query_padding_mask = torch.ones(
                batch_size, seq_len_q, device=device, dtype=torch.bool)
            key_padding_mask = torch.ones(
                batch_size, seq_len_k, device=device, dtype=torch.bool)

            softmax_mask = self.convert_flash_attn_S_to_softmax(
                dbug_mask, seq_len_q, seq_len_k, query_padding_mask, key_padding_mask,
                causal=is_causal)[:, :, :seq_len_q, :seq_len_k]

            # This is the default implementation for the mask but we need to match CK if we are using it
            dropout_mask = softmax_mask >= 0

            # This logic matches how CK calculates the dropout mask.
            # This is necessary because CK doesn't support passing in custom dropout masks
            # So we use this logic to ensure we are comparing apples to apples.
            if TEST_WITH_CK:
                dropout_mask = (softmax_mask <= int((1.0 - dropout_p) * 255.0)).to(torch.float32)

            # High Precision Math Reference
            out_ref = torch.ops.aten._scaled_dot_product_attention_math(
                query_ref, key_ref, value_ref, dropout_p=dropout_p, is_causal=is_causal,
                scale=scale, dropout_mask=dropout_mask, enable_gqa=enable_gqa)[0]
            # Low Precision Math Reference
            out_lp_ref = torch.ops.aten._scaled_dot_product_attention_math(
                query, key, value, dropout_mask=dropout_mask, dropout_p=dropout_p,
                is_causal=is_causal, scale=scale, enable_gqa=enable_gqa)[0]

        upstream_grad = torch.rand_like(out, requires_grad=False)

        # backward for flash attention on sm86, sm87, and sm89 for headdim >= 193 currently disabled
        if isSM8XDevice or isSM120Device and head_dim in range(193, 256):
            self.assertRaises(RuntimeError, lambda: out.backward(upstream_grad))
            return

        grads = torch.autograd.grad(out, (query, key, value), upstream_grad)
        grads_ref_lp = torch.autograd.grad(out_lp_ref, (query, key, value), upstream_grad)
        grads_ref = torch.autograd.grad(out_ref, (query_ref, key_ref, value_ref), upstream_grad)

        fudge_factors = {
            'out': 4,
            'grad_query': 180.0,
            'grad_key': 16,
            'grad_value': 4,
        }
        if TEST_WITH_ROCM:

            fudge_factors['grad_value'] = 6.0
            if TEST_WITH_CK:
                fudge_factors['out'] = 5.0
                fudge_factors['grad_key'] = 145.0
                fudge_factors['grad_query'] = 855.0  # ck min = 855.0
                if seq_len_k >= 1024:
                    fudge_factors['grad_key'] = 70.0
                if seq_len_k >= 2048:
                    fudge_factors['grad_key'] = 190.0
                    fudge_factors['grad_query'] = 1550.0  # NEW CK MIN
                    if seq_len_q >= 2048:
                        fudge_factors['grad_query'] = 1100.0
                if dtype == torch.float32:
                    fudge_factors['grad_key'] = 90.0
            else:
                fudge_factors['out'] = 6.0
                fudge_factors['grad_key'] = 45.0
                fudge_factors['grad_query'] = 360.0
                if seq_len_k >= 1024:
                    fudge_factors['grad_key'] = 70.0
                if seq_len_k >= 2048:
                    fudge_factors['grad_key'] = 190.0
                    fudge_factors['grad_query'] = 650.0
                    if seq_len_q >= 2048:
                        fudge_factors['grad_query'] = 1100.0
                if dtype == torch.float32:
                    fudge_factors['grad_key'] = 90.0

        check_out_and_grad(
            (out_ref, out_lp_ref, out),
            *zip(grads_ref, grads_ref_lp, grads),
            fudge_factors=fudge_factors,
        )