def test_tp1_fp8_fusions(
    model_name: str,
    matches_fn: Callable[[int], Matches],
    model_kwargs: dict,
    hf_overrides: Callable[[int], dict],
    attn_backend: AttentionBackendCase,
    n_layers: int,
    custom_ops: str,
    inductor_graph_partition: bool,
    use_deepgemm: bool,
    run_e2e_fusion_test,
    monkeypatch,
):
    if use_deepgemm and not current_platform.is_cuda():
        pytest.skip("DeepGemm only supported on CUDA")

    if use_deepgemm and is_flashinfer_fp8_blockscale_gemm_supported():
        # Flashinfer block FP8 GEMM has internal quantization, so it can't
        # be fused with other ops.
        pytest.skip("FlashInfer block FP8 GEMM not supported")
    if use_deepgemm and is_blackwell():
        # TODO(luka) DeepGEMM uses different quants, matching not supported
        #  - on Blackwell, uses a special quant fp8, currently not supported
        pytest.skip("DeepGEMM & quant matching not currently supported")

    matches = matches_fn(n_layers)

    block_fp8 = "qwen" in model_name.lower() or "deepseek" in model_name.lower()
    if block_fp8 and "-quant_fp8" in custom_ops:
        # This is why config forces +quant_fp8 by default
        pytest.skip("native QuantFP8 matching not supported for group quant")

    # Reduce size of model and skip weight loading time
    model_kwargs["hf_overrides"] = hf_overrides(n_layers)
    model_kwargs["load_format"] = "dummy"
    model_kwargs["max_model_len"] = 1024
    model_kwargs["kernel_config"] = {"enable_flashinfer_autotune": False}

    compilation_config = dict(
        use_inductor_graph_partition=inductor_graph_partition,
        custom_ops=custom_ops.split(","),
        pass_config=PassConfig(
            fuse_norm_quant=True,
            fuse_act_quant=True,
            fuse_attn_quant=True,
            enable_qk_norm_rope_fusion=True,
        ),
    )

    use_aiter = current_platform.is_rocm() and ("qwen" in model_name.lower())

    matches_check = [
        "rms_quant_fusion",
        "act_quant_fusion",
        "norm_rope_fusion",
        "attn_quant_fusion",
    ]

    if use_aiter:
        matches_check[0] = "aiter_rms_quant_fusion"

        matches = matches._replace(aiter_rms_quant_fusion=matches.rms_quant_fusion)
        # TODO: enable the `norm_rope_fusion` test,
        # On ROCm norm_rope_fusion is only supported without
        # enabling AITER.
        matches_check.remove("norm_rope_fusion")

    run_e2e_fusion_test(
        model_name,
        matches,
        model_kwargs,
        attn_backend,
        compilation_config,
        matches_check,
        use_deepgemm=use_deepgemm,
        use_aiter=use_aiter,
    )