def run_dynamic_test(
        self,
        score_mask_mod: tuple[Callable, Callable],
        dtype: torch.dtype,
        device,
        B: int = B,
        H: int = H,
        S: int = S,
        D: int = D,
    ):
        if device == "cpu" and dtype is torch.float16:
            dtype = torch.float32

        score_mod, mask_mod = score_mask_mod

        # First batch with original dimensions (B, H, S, D)
        block_mask1 = create_block_mask(mask_mod, 1, 1, S, S, device=device)
        sdpa_partial1 = create_attention(score_mod, block_mask=block_mask1)

        requires_grad = device in DEVICE_SUPPORTS_BACKWARDS

        q1 = torch.randn(
            (B, H, S, D),
            dtype=dtype,
            device=device,
            requires_grad=requires_grad,
        )
        k1 = torch.randn(
            (B, H, S, D),
            dtype=dtype,
            device=device,
            requires_grad=requires_grad,
        )
        v1 = torch.randn(
            (B, H, S, D),
            dtype=dtype,
            device=device,
            requires_grad=requires_grad,
        )
        q1_ref, k1_ref, v1_ref = query_key_value_clones(q1, k1, v1)
        q1_gold, k1_gold, v1_gold = query_key_value_clones(q1, k1, v1, torch.float64)
        ref_out1 = sdpa_partial1(q1_ref, k1_ref, v1_ref)
        golden_out1 = sdpa_partial1(q1_gold, k1_gold, v1_gold)
        if requires_grad:
            backward_grad1 = torch.randn((B, H, S, D), dtype=dtype, device=device)
            golden_out1.backward(backward_grad1.to(torch.float64))
            ref_out1.backward(backward_grad1)

        # Second batch with modified dimensions (B * 2, H, S / 2, D)
        B = int(B * 2)
        S = int(S / 2)
        block_mask2 = create_block_mask(mask_mod, 1, 1, S, S, device=device)
        sdpa_partial2 = create_attention(score_mod, block_mask=block_mask2)

        q2 = torch.randn(
            (B, H, S, D),
            dtype=dtype,
            device=device,
            requires_grad=requires_grad,
        )
        k2 = torch.randn(
            (B, H, S, D),
            dtype=dtype,
            device=device,
            requires_grad=requires_grad,
        )
        v2 = torch.randn(
            (B, H, S, D),
            dtype=dtype,
            device=device,
            requires_grad=requires_grad,
        )
        q2_ref, k2_ref, v2_ref = query_key_value_clones(q2, k2, v2)
        q2_gold, k2_gold, v2_gold = query_key_value_clones(q2, k2, v2, torch.float64)
        ref_out2 = sdpa_partial2(q2_ref, k2_ref, v2_ref)
        golden_out2 = sdpa_partial2(q2_gold, k2_gold, v2_gold)

        if requires_grad:
            backward_grad2 = torch.randn((B, H, S, D), dtype=dtype, device=device)
            golden_out2.backward(backward_grad2.to(torch.float64))
            ref_out2.backward(backward_grad2)

        # Third batch with modified dimensions (B * 2, H, S / 4, D)
        S = int(S / 2)
        block_mask3 = create_block_mask(mask_mod, 1, 1, S, S, device=device)
        sdpa_partial3 = create_attention(score_mod, block_mask=block_mask3)

        q3 = torch.randn(
            (B, H, S, D),
            dtype=dtype,
            device=device,
            requires_grad=requires_grad,
        )
        k3 = torch.randn(
            (B, H, S, D),
            dtype=dtype,
            device=device,
            requires_grad=requires_grad,
        )
        v3 = torch.randn(
            (B, H, S, D),
            dtype=dtype,
            device=device,
            requires_grad=requires_grad,
        )
        q3_ref, k3_ref, v3_ref = query_key_value_clones(q3, k3, v3)
        q3_gold, k3_gold, v3_gold = query_key_value_clones(q3, k3, v3, torch.float64)
        ref_out3 = sdpa_partial3(q3_ref, k3_ref, v3_ref)
        golden_out3 = sdpa_partial3(q3_gold, k3_gold, v3_gold)

        if requires_grad:
            backward_grad3 = torch.randn((B, H, S, D), dtype=dtype, device=device)
            golden_out3.backward(backward_grad3.to(torch.float64))
            ref_out3.backward(backward_grad3)

        # Clear dynamo counters
        torch._dynamo.reset()

        # First compilation with original dimensions
        backend = torch._dynamo.testing.CompileCounterWithBackend("inductor")
        compiled_sdpa1 = torch.compile(sdpa_partial1, backend=backend, dynamic=True)
        compiled_out1 = compiled_sdpa1(q1, k1, v1)

        if requires_grad:
            compiled_out1.backward(backward_grad1)

            self._check_out_and_grad(
                golden_out1,
                ref_out1,
                compiled_out1,
                q1_gold,
                q1_ref,
                q1,
                k1_gold,
                k1_ref,
                k1,
                v1_gold,
                v1_ref,
                v1,
            )
        else:
            self._check_out(golden_out1, ref_out1, compiled_out1)
        self.assertEqual(backend.frame_count, 1)

        # Second compilation with new dimensions
        compiled_sdpa2 = torch.compile(sdpa_partial2, backend=backend, dynamic=True)
        compiled_out2 = compiled_sdpa2(q2, k2, v2)

        if requires_grad:
            compiled_out2.backward(backward_grad2)

            self._check_out_and_grad(
                golden_out2,
                ref_out2,
                compiled_out2,
                q2_gold,
                q2_ref,
                q2,
                k2_gold,
                k2_ref,
                k2,
                v2_gold,
                v2_ref,
                v2,
            )
        else:
            self._check_out(golden_out2, ref_out2, compiled_out2)
        self.assertEqual(backend.frame_count, 1)

        # Third compilation with new dimensions
        compiled_sdpa3 = torch.compile(sdpa_partial3, backend=backend, dynamic=True)
        compiled_out3 = compiled_sdpa3(q3, k3, v3)

        if requires_grad:
            compiled_out3.backward(backward_grad3)

            self._check_out_and_grad(
                golden_out3,
                ref_out3,
                compiled_out3,
                q3_gold,
                q3_ref,
                q3,
                k3_gold,
                k3_ref,
                k3,
                v3_gold,
                v3_ref,
                v3,
            )
        else:
            self._check_out(golden_out3, ref_out3, compiled_out3)
        self.assertEqual(backend.frame_count, 1)