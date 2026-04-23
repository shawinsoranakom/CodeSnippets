def test_mxfp8_nvfp4_scaled_grouped_mm_2d_2d(self, G, M, N, K, format):
        torch.manual_seed(42)

        if format == "mxfp4" and SM120OrLater:
            raise unittest.SkipTest("MXFP4 on CUDA only supported on B200/B300")

        total_K = K  # Alias for clarity, communicating this consists of several groups along this dim
        input_group_end_offsets = generate_jagged_offs(
            G, total_K, multiple_of=32, device="cuda"
        )
        X = torch.randn((M, total_K), dtype=torch.bfloat16, device="cuda") * 0.1
        W = torch.randn((N, total_K), dtype=torch.bfloat16, device="cuda") * 0.01

        xh, xq, x_blocked_scales, x_global_scales = _2d_grouped_tensor_to_blocked_scaled(
            X, M, G, input_group_end_offsets, format=format
        )
        wh, wq, w_blocked_scales, w_global_scales = _2d_grouped_tensor_to_blocked_scaled(
            W, N, G, input_group_end_offsets, format=format
        )

        if format in ["mxfp4", "mxfp8"]:
            kwargs = _build_scaled_grouped_mm_kwargs(
                x_blocked_scales,
                w_blocked_scales,
                input_group_end_offsets,
                format,
            )
        elif format == "nvfp4":
            kwargs = _build_scaled_grouped_mm_kwargs(
                [x_blocked_scales, x_global_scales],
                [w_blocked_scales, w_global_scales],
                input_group_end_offsets,
                format,
            )
        else:
            raise ValueError(f'format must be mxfp8|nvfp4|mxfp4, got "{format}"')

        if format == 'nvfp4':
            if x_global_scales.numel() != w_global_scales.numel():
                raise AssertionError(f"scale numel mismatch: {x_global_scales.numel()} != {w_global_scales.numel()}")
            if x_global_scales.numel() != G:
                raise AssertionError(f"scale numel should be {G}, got {x_global_scales.numel()}")

        # Compute mxfp8 grouped mm output
        y_lp = scaled_grouped_mm_wrap(
            xq,
            wq.transpose(-2, -1),
            **kwargs,
        )

        # bf16 reference output
        y_bf16 = grouped_mm(
            # Note: Reference result should be on reconstructed, not original values.
            #       as-in float(fp4(t)) not t itself.
            xh, wh.t(), offs=input_group_end_offsets, out_dtype=torch.bfloat16
        )

        # Assert no NaNs
        if y_lp.isnan().any():
            raise AssertionError("low-precision output contains NaN")

        # Assert outputs are close
        torch.testing.assert_close(y_lp, y_bf16, atol=8.0e-2, rtol=8.0e-2)