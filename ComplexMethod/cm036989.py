def test_fusion_silu_and_mul_quant(
    num_tokens: int,
    hidden_size: int,
    dtype: torch.dtype,
    model_class: type[
        TestSiluMulFp8QuantModel
        | TestSiluMulNvfp4QuantModel
        | TestSiluMulGroupFp8QuantModel
        | TestSiluMulBlockQuantModel
    ],
    enable_silu_mul_custom_op: bool,
    enable_quant_fp8_custom_op: bool,
    force_kernel: FP8ScaledMMLinearKernel | None,
    monkeypatch: pytest.MonkeyPatch,
):
    if model_class is TestSiluMulNvfp4QuantModel and not is_nvfp4_supported():
        pytest.skip("NVFP4 is not supported on this GPU.")
    if model_class is TestSiluMulGroupFp8QuantModel and not IS_AITER_FOUND:
        pytest.skip("AITER is not supported on this GPU.")
    if (
        isinstance(model_class, partial)
        and model_class.func is TestSiluMulBlockQuantModel
        and is_deep_gemm_supported()
    ):
        pytest.skip("SiluMul+BlockQuant fusion not applicable with DeepGemm")

    torch.set_default_device("cuda")
    torch.set_default_dtype(dtype)

    x = torch.rand(num_tokens, hidden_size * 2)

    # Reshape pass is needed for the fusion pass to work
    custom_ops = ["none"]
    if enable_silu_mul_custom_op:
        custom_ops.append("+silu_and_mul")
    if enable_quant_fp8_custom_op:
        custom_ops.append("+quant_fp8")
    config = VllmConfig(
        compilation_config=CompilationConfig(
            mode=CompilationMode.VLLM_COMPILE,
            custom_ops=custom_ops,
            backend="eager",  # avoid compilation for SiluAndMul and QuantFP8
            pass_config=PassConfig(fuse_act_quant=True, eliminate_noops=True),
        ),
    )

    with set_current_vllm_config(config), monkeypatch.context() as m:
        fusion_passes = [ActivationQuantFusionPass(config)]
        if IS_AITER_FOUND and model_class is TestSiluMulGroupFp8QuantModel:
            from vllm._aiter_ops import rocm_aiter_ops
            from vllm.compilation.passes.fusion.rocm_aiter_fusion import (
                RocmAiterSiluMulFp8GroupQuantFusionPass,
            )

            m.setenv("VLLM_ROCM_USE_AITER", "1")
            rocm_aiter_ops.refresh_env_variables()
            fusion_passes += [RocmAiterSiluMulFp8GroupQuantFusionPass(config)]

        passes = [NoOpEliminationPass(config), *fusion_passes, PostCleanupPass(config)]
        backend = TestBackend(*passes)
        model = model_class(
            hidden_size=hidden_size, force_kernel=force_kernel, x=x, dtype=dtype
        )

        # First dimension dynamic
        torch._dynamo.mark_dynamic(x, 0)

        result = model(x)

        model2 = torch.compile(model, backend=backend)
        result2 = model2(x)

        # Check that it gives the same answer
        if isinstance(model, TestSiluMulFp8QuantModel):
            atol, rtol = 1e-3, 1e-3
        elif isinstance(model, TestSiluMulNvfp4QuantModel):
            atol, rtol = 1e-1, 1e-1
        elif isinstance(
            model, (TestSiluMulGroupFp8QuantModel, TestSiluMulBlockQuantModel)
        ):
            atol, rtol = 5e-2, 5e-2

        torch.testing.assert_close(
            result[0].to(dtype=dtype), result2[0].to(dtype=dtype), atol=atol, rtol=rtol
        )

        assert sum([p.matched_count for p in fusion_passes]) == 1

        # In pre-nodes, quant op should be present and fused kernels should not
        backend.check_before_ops(model.ops_in_model_before())

        # In post-nodes, fused kernels should be present and quant op should not
        backend.check_after_ops(model.ops_in_model_after())