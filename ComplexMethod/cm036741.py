def test_batched_mm(
    num_experts: int,
    max_tokens_per_expert: int,
    K: int,
    N: int,
    dtype: torch.dtype,
    block_shape: list[int] | None,
    per_act_token_quant: bool,
):
    """Note: float8_e4m3fn is not supported on CUDA architecture < 89,
    and those tests will be skipped on unsupported hardware."""
    set_random_seed(7)

    use_fp8_w8a8 = dtype == torch.float8_e4m3fn

    if (dtype == torch.float8_e4m3fn) and not current_platform.has_device_capability(
        89
    ):
        pytest.skip(
            "Triton limitation: fp8e4nv data type is not supported on CUDA arch < 89"
        )

    if (per_act_token_quant or block_shape is not None) and not use_fp8_w8a8:
        pytest.skip("Don't test blocking for non-quantized types.")

    if per_act_token_quant and block_shape is not None:
        pytest.skip("Skip illegal quantization test.")

    if dtype.itemsize == 1:
        act_dtype = torch.bfloat16
        quant_dtype = dtype
    else:
        act_dtype = dtype
        quant_dtype = None

    num_expert_tokens = torch.randint(
        low=0,
        high=max_tokens_per_expert,
        size=(num_experts,),
        device="cuda",
        dtype=torch.int32,
    )

    A, A_q, A_scale = make_quantized_test_activations(
        num_experts,
        max_tokens_per_expert,
        K,
        in_dtype=act_dtype,
        quant_dtype=quant_dtype,
        block_shape=block_shape,
        per_act_token_quant=per_act_token_quant,
    )

    (B, B_q, B_scale, _), _ = make_test_weights(
        num_experts,
        N // 2,
        K,
        in_dtype=act_dtype,
        quant_dtype=quant_dtype,
        block_shape=block_shape,
        per_out_ch_quant=per_act_token_quant,
    )

    out_shape = (num_experts, max_tokens_per_expert, N)
    test_output = torch.zeros(out_shape, dtype=act_dtype, device="cuda")
    ref_output = torch.zeros(out_shape, dtype=act_dtype, device="cuda")
    q_ref_output = torch.zeros(out_shape, dtype=act_dtype, device="cuda")

    compute_tl_dtype = {
        torch.float16: tl.float16,
        torch.bfloat16: tl.bfloat16,
        torch.float32: tl.float32,
    }[test_output.dtype]

    assert A_q.dtype == B_q.dtype

    invoke_moe_batched_triton_kernel(
        A_q,
        B_q,
        test_output,
        num_expert_tokens,
        compute_tl_dtype,
        # Quantization data
        A_scale,
        B_scale,
        None,
        # Quantization schemes
        use_fp8_w8a8,
        False,
        False,
        config={
            "BLOCK_SIZE_M": 16,
            "BLOCK_SIZE_N": 16,
            "BLOCK_SIZE_K": 16 if dtype.itemsize > 1 else 32,
        },
        per_act_token_quant=per_act_token_quant,
        block_shape=block_shape,
    )

    ref_output = native_batched_masked_quant_matmul(
        A,
        B,
        ref_output,
        num_expert_tokens,
    )

    q_ref_output = native_batched_masked_quant_matmul(
        A_q,
        B_q,
        q_ref_output,
        num_expert_tokens,
        A_scale,
        B_scale,
        block_shape,
        per_act_token_quant,
    )

    rtol, atol = {
        torch.float16: (6e-2, 6e-2),
        torch.bfloat16: (6e-2, 6e-2),
        torch.float32: (1e-2, 1e-2),
    }[test_output.dtype]

    torch.testing.assert_close(ref_output, q_ref_output, atol=atol, rtol=rtol)
    torch.testing.assert_close(test_output, q_ref_output, atol=atol, rtol=rtol)