def test_strided_inputs(self, device, dtype: torch.dtype, k_s, v_s, head_dims):
        Hq, Hkv = head_dims
        if Hq % Hkv != 0:
            raise AssertionError(
                f"Expected Hq % Hkv == 0, got {Hq} % {Hkv} = {Hq % Hkv}"
            )
        q1 = torch.randn((B * Hq * D), dtype=dtype, device=device)
        k1 = torch.randn((B * Hkv * S * D * 4), dtype=dtype, device=device)
        v1 = torch.randn((B * Hkv * S * D * 4), dtype=dtype, device=device)

        k_shape = (B, Hkv, S, D)
        v_shape = (B, Hkv, S, D)

        q = q1.view(1, Hq, B, D).transpose(0, 2)

        k_strides, k_offset = k_s(B, Hkv, S, D)
        k_max = [x * (y - 1) for x, y in zip(k_strides, k_shape)]
        if sum(k_max) + k_offset >= B * Hkv * S * D * 4:
            raise AssertionError(
                f"Expected sum(k_max) + k_offset < {B * Hkv * S * D * 4}, got {sum(k_max) + k_offset}"
            )
        if k_strides[-1] != 1:
            raise AssertionError(f"Expected k_strides[-1] == 1, got {k_strides[-1]}")
        k = torch.as_strided(k1, k_shape, k_strides, k_offset)

        v_strides, v_offset = v_s(B, Hkv, S, D)
        v_max = [x * (y - 1) for x, y in zip(v_strides, v_shape)]
        if sum(v_max) + v_offset >= B * Hkv * S * D * 4:
            raise AssertionError(
                f"Expected sum(v_max) + v_offset < {B * Hkv * S * D * 4}, got {sum(v_max) + v_offset}"
            )
        if v_strides[-1] != 1:
            raise AssertionError(f"Expected v_strides[-1] == 1, got {v_strides[-1]}")
        v = torch.as_strided(v1, v_shape, v_strides, v_offset)

        score_mod = _generate_alibi_bias(8)

        sdpa_partial = create_attention(
            score_mod=score_mod,
            block_mask=None,
            enable_gqa=(Hq != Hkv),
        )
        compiled_sdpa = torch.compile(sdpa_partial)
        ref_out = sdpa_partial(q, k, v)
        compiled_out = compiled_sdpa(q, k, v)

        tolerance = Tolerances(atol=2e-1, rtol=2e-1)
        torch.testing.assert_close(
            ref_out, compiled_out, atol=tolerance.atol, rtol=tolerance.rtol
        )

        paged_compiled_out, _ = self.run_paged_attention(
            score_mod, q, k, v, dtype, device=device
        )
        torch.testing.assert_close(
            ref_out, paged_compiled_out, atol=tolerance.atol, rtol=tolerance.rtol
        )