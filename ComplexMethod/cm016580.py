def pick_operations(weight_dtype, compute_dtype, load_device=None, disable_fast_fp8=False, fp8_optimizations=False, model_config=None):
    fp8_compute = comfy.model_management.supports_fp8_compute(load_device) # TODO: if we support more ops this needs to be more granular
    nvfp4_compute = comfy.model_management.supports_nvfp4_compute(load_device)
    mxfp8_compute = comfy.model_management.supports_mxfp8_compute(load_device)

    if model_config and hasattr(model_config, 'quant_config') and model_config.quant_config:
        logging.info("Using mixed precision operations")
        disabled = set()
        if not nvfp4_compute:
            disabled.add("nvfp4")
        if not mxfp8_compute:
            disabled.add("mxfp8")
        if not fp8_compute:
            disabled.add("float8_e4m3fn")
            disabled.add("float8_e5m2")
        return mixed_precision_ops(model_config.quant_config, compute_dtype, disabled=disabled)

    if (
        fp8_compute and
        (fp8_optimizations or PerformanceFeature.Fp8MatrixMultiplication in args.fast) and
        not disable_fast_fp8
    ):
        return fp8_ops

    if (
        PerformanceFeature.CublasOps in args.fast and
        CUBLAS_IS_AVAILABLE and
        weight_dtype == torch.float16 and
        (compute_dtype == torch.float16 or compute_dtype is None)
    ):
        logging.info("Using cublas ops")
        return cublas_ops

    if compute_dtype is None or weight_dtype == compute_dtype:
        return disable_weight_init

    return manual_cast