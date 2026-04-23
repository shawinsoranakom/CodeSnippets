def test_mxfp8_scaled_grouped_mm_2d_3d(self, G, M, N, K, format):
        torch.manual_seed(42)

        if format == "mxfp4" and SM120OrLater:
            raise unittest.SkipTest("MXFP4 on CUDA only supported on B200/B300")

        # Simulate 2d-3d grouped gemm `out = input @ weight.t()`
        # 2D inputs with groups along M, 3D weights.
        block_size = 32
        total_M = M  # Alias for clarity that M dim contains groups.
        X = torch.randn((total_M, K), dtype=torch.bfloat16, device="cuda") * 0.1
        W = torch.randn((G, N, K), dtype=torch.bfloat16, device="cuda") * 0.01
        input_group_end_offsets = generate_jagged_offs(
            G, total_M, multiple_of=32, device="cuda"
        )

        # For each constituent 2d subtensor in the 3d weights, quantize and convert scale to blocked format separately,
        # as they each used for independent gemm in the grouped gemm.
        def _3d_to_blocked_scaled(W, G, format):
            wh_list = []
            wq_list = []
            w_scale_list = []
            w_global_scale_list = []
            for i in range(G):
                if format == "mxfp8":
                    wh, wq, w_scale = _convert_to_mxfp8_with_hp_ref(W[i])
                elif format == "nvfp4":
                    w_scale, wq = to_mxfp(W[i], format="mxfp8")
                    wh, wq, w_scale, w_global_scale = _convert_to_nvfp4_with_hp_ref(W[i])
                    w_global_scale_list.append(w_global_scale)
                elif format == "mxfp4":
                    wh, wq, w_scale = _convert_to_mxfp4_with_hp_ref(W[i])
                else:
                    raise ValueError(f'format must be mxfp8|nvfp4|mxfp4, got "{format}"')

                # Swizzle scaled
                if torch.version.cuda:
                    w_scale = to_blocked(w_scale)

                wh_list.append(wh)
                wq_list.append(wq)
                w_scale_list.append(w_scale)
            wh = torch.stack(wh_list, dim=0).contiguous()
            wq = torch.stack(wq_list, dim=0).contiguous()
            w_scale = torch.stack(w_scale_list, dim=0).contiguous()
            # Global scales only exist for nvfp4
            if len(w_global_scale_list) > 0:
                w_global_scales = torch.stack(w_global_scale_list)
            else:
                w_global_scales = None
            return wh, wq, w_scale, w_global_scales

        wh, wq, w_blocked_scales, w_global_scales = _3d_to_blocked_scaled(W, G, format)

        # For each group along `total_M` in the 2D tensor, quantize and convert scale to blocked format separately,
        # as they each used for independent gemm in the grouped gemm.
        def _2d_to_blocked_scaled(X, K, G, offs, format):
            xh_list = []
            xq_list = []
            x_scale_list = []
            x_global_scale_list = []
            for i in range(G):
                prev_group_end = 0 if i == 0 else input_group_end_offsets[i - 1]
                curr_group_end = input_group_end_offsets[i]
                group_size = curr_group_end - prev_group_end
                if group_size > 0:
                    x_slice = X[prev_group_end:curr_group_end, :]
                    if format == "mxfp8":
                        xh, xq, x_scale = _convert_to_mxfp8_with_hp_ref(x_slice)
                    elif format == "nvfp4":
                        xh, xq, x_scale, x_global_scale = _convert_to_nvfp4_with_hp_ref(x_slice)
                        x_global_scale_list.append(x_global_scale)
                    elif format == "mxfp4":
                        xh, xq, x_scale = _convert_to_mxfp4_with_hp_ref(x_slice)
                    else:
                        raise ValueError(f'format must be mxfp8|nvfp4|mxfp4, got "{format}"')

                    if torch.version.cuda:
                        x_scale = to_blocked(x_scale)
                    xh_list.append(xh)
                    xq_list.append(xq)
                    x_scale_list.append(x_scale)
            xh = torch.cat(xh_list, dim=0).contiguous()
            xq = torch.cat(xq_list, dim=0).contiguous()
            x_scale = torch.cat(x_scale_list, dim=0).contiguous()
            x_scale = x_scale.reshape(-1, K // block_size)
            xq = xq.view(-1, xq.shape[-1])
            xh = xh.view(-1, xh.shape[-1])

            x_global_scales = None
            if len(x_global_scale_list) > 0:
                x_global_scales = torch.stack(x_global_scale_list)

            return xh, xq, x_scale, x_global_scales

        xh, xq, x_blocked_scales, x_global_scales = _2d_to_blocked_scaled(X, K, G, input_group_end_offsets, format)

        if format in ["mxfp8", "mxfp4"]:
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
            raise ValueError(f'format must be mxfp8|nvfp4, got "{format}"')

        if format == 'nvfp4':
            if x_global_scales.numel() != w_global_scales.numel():
                raise AssertionError(f"scale numel mismatch: {x_global_scales.numel()} != {w_global_scales.numel()}")
            if x_global_scales.numel() != G:
                raise AssertionError(f"scale numel should be {G}, got {x_global_scales.numel()}")

        # Compute low-precision grouped gemm.
        y_lp = scaled_grouped_mm_wrap(
            xq,
            wq.transpose(-2, -1),
            **kwargs
        )

        # Compute reference bf16 grouped gemm.
        # Note: Reference result should be on reconstructed, not original values.
        #       as-in float(fp4(t)) not t itself.
        y_bf16 = grouped_mm(
            xh,
            wh.transpose(-2, -1),
            offs=input_group_end_offsets,
            out_dtype=torch.bfloat16,
        )

        # Assert outputs are close.
        torch.testing.assert_close(y_lp, y_bf16, atol=8.0e-2, rtol=8.0e-2)