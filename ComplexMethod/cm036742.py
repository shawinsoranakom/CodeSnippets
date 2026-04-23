def test_fused_moe_batched_experts(
    m: int,
    n: int,
    k: int,
    e: int,
    topk: int,
    dtype: torch.dtype,
    per_act_token_quant: bool,
    block_shape: list[int] | None,
    input_scales: bool,
    workspace_init,
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

    if topk > e:
        pytest.skip("topk > e")

    if not use_fp8_w8a8 and (per_act_token_quant or block_shape is not None):
        pytest.skip("Skip quantization test for non-quantized type")

    if per_act_token_quant and block_shape is not None:
        pytest.skip("Skip illegal quantization test.")

    a = torch.randn((m, k), device="cuda", dtype=torch.bfloat16) / 10
    score = torch.randn((m, e), device="cuda", dtype=torch.bfloat16)

    if dtype.itemsize == 1:
        act_dtype = torch.bfloat16
        quant_dtype = dtype
    else:
        act_dtype = dtype
        quant_dtype = None

    (w1_16, w1, w1_s, _), (w2_16, w2, w2_s, _) = make_test_weights(
        e,
        n,
        k,
        block_shape=block_shape,
        in_dtype=act_dtype,
        quant_dtype=quant_dtype,
        per_out_ch_quant=per_act_token_quant,
    )

    if input_scales and quant_dtype is not None:
        a1_scale = torch.tensor(1, device="cuda", dtype=torch.float32)
        a2_scale = torch.tensor(1, device="cuda", dtype=torch.float32)
    else:
        a1_scale = None
        a2_scale = None

    with set_current_vllm_config(vllm_config):
        topk_weight, topk_ids, _ = fused_topk(a, score, topk, False)

        baseline_output = torch_experts(
            a,
            w1,
            w2,
            topk_weight,
            topk_ids,
            w1_scale=w1_s,
            w2_scale=w2_s,
            a1_scale=a1_scale,
            a2_scale=a2_scale,
            quant_dtype=quant_dtype,
            per_act_token_quant=per_act_token_quant,
            block_shape=block_shape,
        )

        batched_output = naive_batched_moe(
            a,
            w1,
            w2,
            topk_weight,
            topk_ids,
            w1_scale=w1_s,
            w2_scale=w2_s,
            a1_scale=a1_scale,
            a2_scale=a2_scale,
            quant_dtype=quant_dtype,
            per_act_token_quant=per_act_token_quant,
            block_shape=block_shape,
        )

        triton_output = batched_moe(
            a,
            w1,
            w2,
            topk_weight,
            topk_ids,
            w1_scale=w1_s,
            w2_scale=w2_s,
            a1_scale=a1_scale,
            a2_scale=a2_scale,
            quant_dtype=quant_dtype,
            per_act_token_quant=per_act_token_quant,
            block_shape=block_shape,
        )

    torch.testing.assert_close(batched_output, baseline_output, atol=3e-2, rtol=2e-2)

    torch.testing.assert_close(triton_output, batched_output, atol=2e-2, rtol=2e-2)