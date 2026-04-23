def test_silu_mul_fp8_quant_deep_gemm(E: int, T: int, H: int, fp8_type: torch.dtype):
    group_size = 128
    set_random_seed(42)

    tokens_per_expert = torch.randint(
        low=0,
        high=T,
        size=(E,),
        dtype=torch.int32,
        device="cuda",
    )

    # Input tensor of shape (E, T, 2*H)
    y = token_random(E, T, 2 * H, tokens_per_expert)

    gate = y[..., :H].to(torch.bfloat16)
    up = y[..., H:].to(torch.bfloat16)

    scale_fmts = [
        DeepGemmQuantScaleFMT.FLOAT32,
        DeepGemmQuantScaleFMT.FLOAT32_CEIL_UE8M0,
    ]
    # UE8M0 (int32 packed) scales require the C++ kernel which is
    # not available on ROCm (#ifndef USE_ROCM).
    # https://github.com/ROCm/aiter/issues/2420
    if current_platform.is_cuda():
        scale_fmts.append(DeepGemmQuantScaleFMT.UE8M0)

    # Run the SiLU V2 kernel
    for scale_fmt in scale_fmts:
        y_q, y_s = persistent_masked_m_silu_mul_quant(
            y,
            tokens_per_expert,
            group_size=group_size,
            quant_scale_fmt=scale_fmt,
        )

        ref_y_q, ref_y_s = ref_with_scale_fmt(
            E, T, H, group_size, tokens_per_expert, gate, up, scale_fmt=scale_fmt
        )

        # deepgemm scales transform
        dg_scales = None
        if (
            has_deep_gemm()
            and current_platform.has_device_capability(100)
            and scale_fmt == DeepGemmQuantScaleFMT.UE8M0
        ):
            _q, _s = ref_with_scale_fmt(
                E,
                T,
                H,
                group_size,
                tokens_per_expert,
                gate,
                up,
                scale_fmt=DeepGemmQuantScaleFMT.FLOAT32_CEIL_UE8M0,
            )
            dg_scales = transform_sf_into_required_layout(
                sf=_s,
                mn=_q.size(1),
                k=_q.size(2),
                recipe=(1, 128, 128),
                num_groups=_q.size(0),
                is_sfa=True,
            )

        expected_scale_dtype = (
            torch.int32 if scale_fmt == DeepGemmQuantScaleFMT.UE8M0 else torch.float32
        )
        assert y_s.dtype == expected_scale_dtype
        assert ref_y_s.dtype == expected_scale_dtype

        for e in range(E):
            nt = tokens_per_expert[e].item()

            if current_platform.is_rocm():
                # On ROCm the Triton fallback kernel uses f32 math
                # intrinsics (tl.exp) that may differ from PyTorch's
                # torch.exp by 1 ULP.  At FP8 quantization
                # boundaries this can flip one representable value.
                # Allow 1 FP8 quantum of tolerance.
                torch.testing.assert_close(
                    y_q[e, :nt].to(torch.float32),
                    ref_y_q[e, :nt].to(torch.float32),
                    atol=32.0,
                    rtol=0.2,
                )
            else:
                torch.testing.assert_close(
                    y_q[e, :nt].to(torch.float32),
                    ref_y_q[e, :nt].to(torch.float32),
                )

            if scale_fmt == DeepGemmQuantScaleFMT.UE8M0:
                G = H // group_size
                y_s_sliced = as_uint8(y_s[e])
                ref_s_sliced = as_uint8(ref_y_s[e])
                torch.testing.assert_close(y_s_sliced[:nt, :G], ref_s_sliced[:nt, :G])
                if dg_scales is not None:
                    dg_sliced = as_uint8(dg_scales[e])
                    torch.testing.assert_close(y_s_sliced[:nt, :G], dg_sliced[:nt, :G])
            else:
                torch.testing.assert_close(
                    y_s[e, :nt],
                    ref_y_s[e, :nt],
                )