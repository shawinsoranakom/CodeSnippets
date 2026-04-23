def test_fusion_rmsnorm_quant(
    dtype,
    hidden_size,
    num_tokens,
    eps,
    kernel_groupshape,
    enable_rms_norm_custom_op,
    enable_quant_fp8_custom_op,
):
    force_kernel, group_shape = kernel_groupshape

    if not enable_quant_fp8_custom_op and group_shape.is_per_group():
        pytest.skip("Unsupported unwrapped quant fp8 op for blockwise quantization")

    if group_shape == GroupShape(1, 64) and (
        cutlass_block_fp8_supported() or is_deep_gemm_supported()
    ):
        pytest.skip("Unsupported group shape 64 for CUTLASS/DeepGemm")

    # TODO(quant-rms-fusion): DeepGEMM UE8M0 activation quant on B200 lowers
    # to a packed int32-scale op (per_token_group_quant_fp8_packed_for_deepgemm),
    # but the rms+quant fusion pattern only matches the fp32-scale variant, so
    # the fused output gets a mismatched scale layout and produces NaN. Only
    # reproduces on bf16 (DeepGEMM UE8M0 on B200 is bf16-only).
    # To re-enable: make rms_norm_per_block_quant emit packed UE8M0 scales
    # and extend the fusion pattern to rewrite the packed activation quant.
    deepgemm_kernels = (
        DeepGemmFp8BlockScaledMMKernel,
        FlashInferFp8DeepGEMMDynamicBlockScaledKernel,
    )
    if (
        dtype == torch.bfloat16
        and force_kernel in deepgemm_kernels
        and is_deep_gemm_e8m0_used()
    ):
        pytest.skip(
            "rms+quant fusion does not yet match the packed UE8M0 DeepGEMM path"
        )

    custom_ops = []
    if enable_rms_norm_custom_op:
        custom_ops.append("+rms_norm")
    if enable_quant_fp8_custom_op:
        custom_ops.append("+quant_fp8")

    vllm_config = VllmConfig(
        model_config=ModelConfig(dtype=dtype),
        compilation_config=CompilationConfig(
            mode=CompilationMode.VLLM_COMPILE,
            custom_ops=custom_ops,
            pass_config=PassConfig(
                fuse_norm_quant=True, fuse_act_quant=True, eliminate_noops=True
            ),
        ),
    )

    with (
        vllm.config.set_current_vllm_config(vllm_config),
        vllm_config.kernel_config.ir_op_priority.set_priority(),
    ):
        # Setup device before model creation
        torch.set_default_device("cuda")
        torch.set_default_dtype(dtype)
        torch.manual_seed(1)

        fusion_pass = RMSNormQuantFusionPass(vllm_config)

        model = TestModel(
            hidden_size=hidden_size,
            eps=eps,
            force_kernel=force_kernel,
            group_shape=group_shape,
            dtype=dtype,
            use_aiter_fusion=False,
            use_aiter_quant=False,
        )

        backend, _ = _run_fusion_test(
            model, fusion_pass, vllm_config, dtype, hidden_size, num_tokens
        )
        backend.check_before_ops(
            model.ops_in_model_before_partial(), fully_replaced=False
        )

        # If RMSNorm custom op is disabled (native/torch impl used),
        # there's a risk that the fused add doesn't get included in the
        # replacement and only the rms part gets fused with quant.
        # Hence, we check only 2 add nodes are left (final fused rmsnorm add).
        if not enable_rms_norm_custom_op:
            n_add_nodes = lambda g: sum(1 for _ in find_op_nodes(torch.ops.aten.add, g))
            # rms_norm is IR, not included
            # 6 = 3x2 (3xRMS_ADD, 2 each)
            assert n_add_nodes(backend.graph_pre_pass) == 6
            assert n_add_nodes(backend.graph_post_pass) == 2