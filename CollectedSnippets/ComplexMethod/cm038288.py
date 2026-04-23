def can_implement(cls, c: FP8ScaledMMLinearLayerConfig) -> tuple[bool, str | None]:
        is_ptpc = (
            c.activation_quant_key.scale.group_shape.is_per_token()
            and c.weight_quant_key.scale.group_shape.is_per_channel()
        )
        if c.weight_shape is None:
            return False, "weight_shape is required for Aiter kernels"
        N, K = c.weight_shape
        fp8_dtype = current_platform.fp8_dtype()

        if c.out_dtype is not torch.bfloat16:
            return False, "requires bfloat16 output dtype."

        if not is_ptpc:
            return (
                False,
                "requires per token activation scales and per channel weight scales.",
            )

        if not (N % 16 == 0 and K % 16 == 0):
            return (
                False,
                f"requires N and K dimensions divisible by 16, received "
                f"N={N} and K={K}.",
            )

        # Aiter's shuffled per-token Gemm performs better than torch only when its
        # tuned.
        if not rocm_aiter_ops.is_shuffled_per_token_w8a8_gemm_tuned(N, K, fp8_dtype):
            return (
                False,
                f"requires a tuned configuration for N: {N} and K: {K} "
                f"and fp8 dtype {fp8_dtype}.",
            )

        return True, None