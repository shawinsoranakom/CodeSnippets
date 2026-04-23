def run_benchmarks(
    num_tokens: int,
    hidden_dim: int,
    dtype: torch.dtype,
    use_residual: bool,
    allreduce_params: FlashInferFusedAllReduceParams | None,
    workspaces: dict,
    quant_modes: set[str],
    no_oneshot: bool,
):
    """Run all benchmarks for given configuration.

    Args:
        allreduce_params: Shared parameters for FlashInfer fused allreduce.
        workspaces: Dict mapping backend name ("trtllm", "mnnvl") to workspace.
        quant_modes: Set of quantization modes: "none", "fp8", "fp4".
    """
    (
        input_tensor,
        norm_out,
        residual,
        rms_gamma,
        scale_fp8,
        quant_out_fp8,
        scale_fp4,
        fp4_quant_out,
        fp4_output_scale,
    ) = create_test_tensors(num_tokens, hidden_dim, dtype, use_residual)

    rms_eps = 1e-6
    results = {}
    use_oneshot_options = [False] if no_oneshot else [True, False]

    if "none" in quant_modes:
        # Standard AllReduce + RMSNorm
        # Re-create VllmFusedAllreduce per config so CustomOp binds the
        # correct forward method (native vs custom kernel).
        for custom_op in ["-rms_norm", "+rms_norm"]:
            with set_current_vllm_config(
                VllmConfig(compilation_config=CompilationConfig(custom_ops=[custom_op]))
            ):
                try:
                    vllm_fused_allreduce = VllmFusedAllreduce(hidden_dim, dtype)
                    suffix = (
                        "_custom_rms_norm" if "+" in custom_op else "_native_rms_norm"
                    )
                    time_ms = benchmark_operation(
                        vllm_fused_allreduce.allreduce_rmsnorm,
                        input_tensor,
                        residual=residual,
                    )
                    results[f"standard_allreduce_{suffix}"] = time_ms
                except Exception as e:
                    logger.error("Standard AllReduce+RMSNorm failed: %s", e)
                    results[f"standard_allreduce_{suffix}"] = float("inf")

        # Standard AllReduce + RMSNorm Native Compiled
        with set_current_vllm_config(
            VllmConfig(compilation_config=CompilationConfig(custom_ops=["-rms_norm"]))
        ):
            try:
                vllm_fused_allreduce = VllmFusedAllreduce(hidden_dim, dtype)
                standard_allreduce_rmsnorm_native_compiled = torch.compile(
                    vllm_fused_allreduce.allreduce_rmsnorm,
                    fullgraph=True,
                    dynamic=False,
                )
                time_ms = benchmark_operation(
                    standard_allreduce_rmsnorm_native_compiled,
                    input_tensor,
                    residual=residual,
                )
                results["standard_allreduce_rmsnorm_native_compiled"] = time_ms
            except Exception as e:
                logger.error("Standard AllReduce+RMSNorm Native Compiled failed: %s", e)
                results["standard_allreduce_rmsnorm_native_compiled"] = float("inf")

        # FlashInfer Fused AllReduce + RMSNorm (all backends)
        for backend, workspace in workspaces.items():
            for use_oneshot in use_oneshot_options:
                suffix = "_oneshot" if use_oneshot else "_twoshot"
                key = f"flashinfer_{backend}_fused_allreduce_rmsnorm{suffix}"
                try:
                    time_ms = benchmark_operation(
                        flashinfer_fused_allreduce_rmsnorm,
                        input_tensor,
                        residual=residual,
                        norm_out=norm_out,
                        rms_gamma=rms_gamma,
                        rms_eps=rms_eps,
                        allreduce_params=allreduce_params,
                        workspace=workspace,
                        use_oneshot=use_oneshot,
                    )
                    results[key] = time_ms
                except Exception as e:
                    logger.error(
                        "FlashInfer (%s) Fused AllReduce+RMSNorm failed: %s",
                        backend,
                        e,
                    )
                    results[key] = float("inf")

    if "fp8" in quant_modes:
        # Standard AllReduce + RMSNorm + FP8 Quant
        for rms_norm_custom_op in ["-rms_norm", "+rms_norm"]:
            suffix = (
                "_custom_rms_norm" if "+" in rms_norm_custom_op else "_native_rms_norm"
            )
            for quant_fp8_custom_op in ["-quant_fp8", "+quant_fp8"]:
                op_suffix = suffix + (
                    "_custom_quant_fp8"
                    if "+" in quant_fp8_custom_op
                    else "_native_quant_fp8"
                )
                with set_current_vllm_config(
                    VllmConfig(
                        compilation_config=CompilationConfig(
                            custom_ops=[rms_norm_custom_op, quant_fp8_custom_op]
                        )
                    )
                ):
                    try:
                        vllm_fused_allreduce = VllmFusedAllreduce(hidden_dim, dtype)
                        time_ms = benchmark_operation(
                            vllm_fused_allreduce.allreduce_rmsnorm_fp8_quant,
                            input_tensor,
                            residual=residual,
                            scale_factor=scale_fp8,
                        )
                        results[f"standard_allreduce{op_suffix}"] = time_ms
                    except Exception as e:
                        logger.error("Standard AllReduce+RMSNorm+FP8 failed: %s", e)
                        results[f"standard_allreduce{op_suffix}"] = float("inf")

        # Standard AllReduce + RMSNorm + FP8 Quant Native Compiled
        with set_current_vllm_config(
            VllmConfig(
                compilation_config=CompilationConfig(
                    custom_ops=["-rms_norm", "-quant_fp8"]
                )
            )
        ):
            try:
                vllm_fused_allreduce = VllmFusedAllreduce(hidden_dim, dtype)
                standard_allreduce_rmsnorm_fp8_quant_native_compiled = torch.compile(
                    vllm_fused_allreduce.allreduce_rmsnorm_fp8_quant,
                    fullgraph=True,
                    dynamic=False,
                )
                time_ms = benchmark_operation(
                    standard_allreduce_rmsnorm_fp8_quant_native_compiled,
                    input_tensor,
                    residual=residual,
                    scale_factor=scale_fp8,
                )
                results["standard_allreduce_rmsnorm_fp8_quant_native_compiled"] = (
                    time_ms
                )
            except Exception as e:
                logger.error(
                    "Standard AllReduce+RMSNorm+FP8 Native Compiled failed: %s", e
                )
                results["standard_allreduce_rmsnorm_fp8_quant_native_compiled"] = float(
                    "inf"
                )

        # FlashInfer Fused AllReduce + RMSNorm + FP8 Quant (trtllm only)
        if "trtllm" in workspaces:
            trtllm_ws = workspaces["trtllm"]
            for use_oneshot in use_oneshot_options:
                suffix = "_oneshot" if use_oneshot else "_twoshot"
                key = f"flashinfer_trtllm_fused_allreduce_rmsnorm_fp8_quant{suffix}"
                try:
                    time_ms = benchmark_operation(
                        flashinfer_fused_allreduce_rmsnorm_fp8_quant,
                        input_tensor,
                        norm_out=norm_out,
                        residual=residual,
                        rms_gamma=rms_gamma,
                        rms_eps=rms_eps,
                        scale_factor=scale_fp8,
                        quant_out=quant_out_fp8,
                        allreduce_params=allreduce_params,
                        workspace=trtllm_ws,
                        use_oneshot=use_oneshot,
                    )
                    results[key] = time_ms
                except Exception as e:
                    logger.error(
                        "FlashInfer (trtllm) Fused AllReduce+RMSNorm+FP8 failed: %s",
                        e,
                    )
                    results[key] = float("inf")

    if "fp4" in quant_modes and current_platform.has_device_capability(100):
        # Standard AllReduce + RMSNorm + FP4 Quant
        for rms_norm_custom_op in ["-rms_norm", "+rms_norm"]:
            suffix = (
                "_custom_rms_norm" if "+" in rms_norm_custom_op else "_native_rms_norm"
            )
            with set_current_vllm_config(
                VllmConfig(
                    compilation_config=CompilationConfig(
                        custom_ops=[rms_norm_custom_op]
                    )
                )
            ):
                try:
                    vllm_fused_allreduce = VllmFusedAllreduce(hidden_dim, dtype)
                    time_ms = benchmark_operation(
                        vllm_fused_allreduce.allreduce_rmsnorm_fp4_quant,
                        input_tensor,
                        residual=residual,
                        input_global_scale=scale_fp4,
                        quant_out=fp4_quant_out,
                        output_scale=fp4_output_scale,
                    )
                    results[f"standard_allreduce_{suffix}_fp4_quant"] = time_ms
                except Exception as e:
                    logger.error("Standard AllReduce+RMSNorm+FP4 failed: %s", e)
                    results[f"standard_allreduce_{suffix}_fp4_quant"] = float("inf")

        # Standard AllReduce + RMSNorm + FP4 Quant Native Compiled
        with set_current_vllm_config(
            VllmConfig(compilation_config=CompilationConfig(custom_ops=["-rms_norm"]))
        ):
            try:
                vllm_fused_allreduce = VllmFusedAllreduce(hidden_dim, dtype)
                standard_allreduce_rmsnorm_fp4_quant_native_compiled = torch.compile(
                    vllm_fused_allreduce.allreduce_rmsnorm_fp4_quant,
                    fullgraph=True,
                    dynamic=False,
                )
                time_ms = benchmark_operation(
                    standard_allreduce_rmsnorm_fp4_quant_native_compiled,
                    input_tensor,
                    residual=residual,
                    quant_out=fp4_quant_out,
                    input_global_scale=scale_fp4,
                    output_scale=fp4_output_scale,
                )
                results["standard_allreduce_rmsnorm_fp4_quant_native_compiled"] = (
                    time_ms
                )
            except Exception as e:
                logger.error(
                    "Standard AllReduce+RMSNorm+FP4 Native Compiled failed: %s", e
                )
                results["standard_allreduce_rmsnorm_fp4_quant_native_compiled"] = float(
                    "inf"
                )

        # FlashInfer Fused AllReduce + RMSNorm + FP4 Quant (trtllm only)
        if "trtllm" in workspaces:
            trtllm_ws = workspaces["trtllm"]
            for use_oneshot in use_oneshot_options:
                suffix = "_oneshot" if use_oneshot else "_twoshot"
                key = f"flashinfer_trtllm_fused_allreduce_rmsnorm_fp4_quant{suffix}"
                try:
                    time_ms = benchmark_operation(
                        flashinfer_fused_allreduce_rmsnorm_fp4_quant,
                        input_tensor,
                        residual=residual,
                        norm_out=norm_out,
                        rms_gamma=rms_gamma,
                        rms_eps=rms_eps,
                        input_global_scale=scale_fp4,
                        allreduce_params=allreduce_params,
                        workspace=trtllm_ws,
                        quant_out=fp4_quant_out,
                        output_scale=fp4_output_scale,
                        use_oneshot=use_oneshot,
                    )
                    results[key] = time_ms
                except Exception as e:
                    logger.error(
                        "FlashInfer (trtllm) Fused AllReduce+RMSNorm+FP4 failed: %s",
                        e,
                    )
                    results[key] = float("inf")

    return results