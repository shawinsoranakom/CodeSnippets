def test_fused_attention_vs_math_ref_grads_cudagraph(self, device, batch_size: int,
                                                         seq_len_q: int, seq_len_k: int,
                                                         head_dim: int,
                                                         is_causal: bool,
                                                         dropout_p: float,
                                                         dtype: torch.dtype,
                                                         scale: str,
                                                         fused_kernel: SDPBackend):
        def _get_mem_eff_drop_mask(batch_size, n_heads, q_len, kv_len, dropout_p, seed, offset, device=device):
            mask = torch.empty((batch_size, n_heads, q_len, kv_len), device=device, dtype=torch.float32)
            rand_uniform = torch._fill_mem_eff_dropout_mask_(mask, dropout_p, seed, offset)
            # On ROCM _fill_mem_eff_dropout_mask fills 0.5 if (prng > p) otherwise -0.5 to the tensor
            tester_p = dropout_p if not TEST_WITH_ROCM else 0.0
            mask = (rand_uniform > tester_p).to(torch.float32)
            return mask

        def get_dropout_mask(output, fused_kernel, batch_size, n_heads, q_len, kv_len, dropout_p, device=device):
            if fused_kernel == SDPBackend.EFFICIENT_ATTENTION:
                output_seed, output_offset = output_tuple[2], output_tuple[3]
                output_seed = output_seed.item()
                output_offset = output_offset.item()
                return _get_mem_eff_drop_mask(batch_size, n_heads, q_len, kv_len,
                                              dropout_p, output_seed, output_offset, device=device)
            else:
                # Build dropout_mask
                dbug_mask = output_tuple[-1]
                query_padding_mask = torch.ones(
                    batch_size, seq_len_q, device=device, dtype=torch.bool)
                key_padding_mask = torch.ones(
                    batch_size, seq_len_k, device=device, dtype=torch.bool)

                softmax_mask = self.convert_flash_attn_S_to_softmax(
                    dbug_mask, seq_len_q, seq_len_k, query_padding_mask, key_padding_mask,
                    causal=is_causal)[:, :, :seq_len_q, :seq_len_k]
                dropout_mask = softmax_mask >= 0
                return dropout_mask

        if fused_kernel == SDPBackend.FLASH_ATTENTION and is_causal and seq_len_q != seq_len_k:
            self.skipTest("Flash V2 does not accept is_casual when seq_len_q != seq_len_k")

        seed = 42
        n_heads = 4
        query = torch.rand(batch_size, n_heads, seq_len_q, head_dim,
                           device=device, dtype=dtype, requires_grad=True)
        key = torch.rand(batch_size, n_heads, seq_len_k, head_dim, device=device,
                         dtype=dtype, requires_grad=True)
        value = torch.rand(batch_size, n_heads, seq_len_k, head_dim,
                           device=device, dtype=dtype, requires_grad=True)

        fused_op = (torch.ops.aten._scaled_dot_product_efficient_attention
                    if fused_kernel == SDPBackend.EFFICIENT_ATTENTION else torch.ops.aten._scaled_dot_product_flash_attention
                    if fused_kernel == SDPBackend.FLASH_ATTENTION else torch.ops.aten._scaled_dot_product_cudnn_attention)

        higher_precision_dtype = torch.float64 if dtype == torch.float32 else torch.float32
        query_ref, key_ref, value_ref = query_key_value_clones(query, key, value, dtype=higher_precision_dtype)

        # warmup
        s = torch.cuda.Stream()
        s.wait_stream(torch.cuda.current_stream())
        # Set the global seed before capture
        torch.manual_seed(seed)
        kwargs = {"dropout_p": dropout_p, "is_causal": is_causal}
        if fused_kernel == SDPBackend.EFFICIENT_ATTENTION:
            kwargs["compute_log_sumexp"] = True
            kwargs["attn_bias"] = None
        if fused_kernel == SDPBackend.FLASH_ATTENTION:
            kwargs['return_debug_mask'] = dropout_p > 0.0
        if fused_kernel == SDPBackend.CUDNN_ATTENTION:
            kwargs["compute_log_sumexp"] = True
            kwargs["attn_bias"] = None
            if "return_debug_mask" in kwargs:
                kwargs.pop("return_debug_mask")
        with torch.cuda.stream(s):
            # Create real output
            output_tuple = fused_op(query, key, value, **kwargs)

        torch.cuda.current_stream().wait_stream(s)
        out = output_tuple[0]
        upstream_grad = torch.rand_like(out, requires_grad=False)
        s.wait_stream(torch.cuda.current_stream())
        with torch.cuda.stream(s):
            out.backward(upstream_grad)
        for x in (query, key, value):
            x.grad = None
        g = torch.cuda.CUDAGraph()
        # Create real output
        with torch.cuda.graph(g):
            torch.rand_like(query, device=query.device)  # test non-zero intragraph offset
            # Create real output
            output_tuple = fused_op(query, key, value, **kwargs)
            if not all(not isinstance(o, torch.Tensor) or o.is_cuda for o in output_tuple):
                raise AssertionError("expected all tensor outputs to be on cuda")
        g.replay()
        out_first = output_tuple[0].clone()
        g.replay()
        out = output_tuple[0]
        if dropout_p == 0.0:
            self.assertEqual(out_first, out, atol=0, rtol=0)
        else:
            # replays produce different results
            self.assertNotEqual(out_first, out)

        with sdpa_kernel(backends=[SDPBackend.MATH]):
            if dropout_p == 0.0:
                # High Precision Math Reference
                out_ref = F.scaled_dot_product_attention(query_ref, key_ref, value_ref,
                                                         dropout_p=dropout_p, is_causal=is_causal)
                # Low Precision Math Reference
                out_lp_ref = F.scaled_dot_product_attention(query, key, value,
                                                            dropout_p=dropout_p, is_causal=is_causal)
            # cuDNN attention doesn't support returning dropout mask
            elif fused_kernel != SDPBackend.CUDNN_ATTENTION:
                # Create the dropout_mask
                dropout_mask = get_dropout_mask(output_tuple, fused_kernel, batch_size,
                                                n_heads, seq_len_q, seq_len_k, dropout_p, device)
                # High Precision Math Reference
                out_ref = torch.ops.aten._scaled_dot_product_attention_math(
                    query_ref, key_ref, value_ref, dropout_p=dropout_p, is_causal=is_causal,
                    dropout_mask=dropout_mask)[0]
                # Low Precision Math Reference
                out_lp_ref = torch.ops.aten._scaled_dot_product_attention_math(
                    query, key, value, dropout_p=dropout_p, is_causal=is_causal,
                    dropout_mask=dropout_mask)[0]

        g1 = torch.cuda.CUDAGraph()
        with torch.cuda.graph(g1):
            grads = torch.autograd.grad(out, (query, key, value), upstream_grad)
        g1.replay()
        if fused_kernel != SDPBackend.CUDNN_ATTENTION or dropout_p == 0.0:
            grads_ref_lp = torch.autograd.grad(out_lp_ref, (query, key, value), upstream_grad)
            grads_ref = torch.autograd.grad(out_ref, (query_ref, key_ref, value_ref), upstream_grad)

            fudge_factors = {
                'out': 3.0,
                'grad_query': 110.0,
                'grad_key': 8.0,
                'grad_value': 3.0,
            }
            if TEST_WITH_ROCM:
                fudge_factors['out'] = 6.0
                fudge_factors['grad_value'] = 6.0
            check_out_and_grad(
                (out_ref, out_lp_ref, out),
                *zip(grads_ref, grads_ref_lp, grads),
                fudge_factors=fudge_factors
            )