def gemm_with_dynamic_quant(
        x: torch.Tensor,
        weight: torch.Tensor,
        weight_scale: torch.Tensor,
        rocm_use_aiter_fp4_asm_gemm: bool = False,
        out_dtype: torch.dtype | None = torch.bfloat16,
        x_scales: torch.Tensor | None = None,
    ) -> torch.Tensor:
        M = x.shape[0]
        N = weight.shape[0]
        K = weight.shape[1]
        if rocm_use_aiter_fp4_asm_gemm:
            if M <= 64 and rocm_aiter_ops.is_triton_gemm_afp4wfp4_presh_ws_tuned(N, K):
                if x_scales is None:
                    # use hip quant kernel for performance
                    if M >= 32:
                        x_q, x_s = per_1x32_f4_quant_hip(x, shuffle=True)
                    else:
                        x_q, x_s = per_1x32_f4_quant_hip(x, shuffle=False)
                else:
                    x_q = x
                    x_s = x_scales

                if M >= 32:
                    x_s = x_s.view(torch.uint8).view(x_s.shape[0] // 32, -1)
                else:
                    x_s = x_s[:M, ...].view(torch.uint8)

                y = torch.empty(M, N, device=x_q.device, dtype=out_dtype)
                gemm_afp4wfp4_preshuffled_weight_scales(
                    x_q.view(torch.uint8),
                    weight.view(torch.uint8).view(weight.shape[0] // 16, -1),
                    x_s,
                    weight_scale.view(torch.uint8).view(
                        weight_scale.shape[0] // 32, -1
                    ),
                    out_dtype,
                    y,
                )
            else:
                if x_scales is None:
                    # use hip quant kernel for performance
                    x_q, x_s = per_1x32_f4_quant_hip(x, shuffle=True)
                else:
                    x_q = x
                    x_s = x_scales

                # 32 alignment is enough for dim0 padding of output for
                # gemm_a4w4 kernel
                y = torch.empty(
                    (M + 31) // 32 * 32,
                    weight.shape[0],
                    device=x_q.device,
                    dtype=out_dtype,
                )

                gemm_a4w4(
                    x_q,
                    weight.view(x_q.dtype),
                    x_s,
                    weight_scale.view(x_s.dtype),
                    y,
                    bpreshuffle=True,
                )
            return y[:M]
        else:
            if x_scales is None:
                x_q, x_s = dynamic_mxfp4_quant(x)
            else:
                x_q = x
                x_s = x_scales
            y = torch.empty(
                x_q.shape[0], weight.shape[0], device=x_q.device, dtype=out_dtype
            )

            gemm_afp4wfp4(x_q, weight, x_s, weight_scale.T, out_dtype, y)
            return y