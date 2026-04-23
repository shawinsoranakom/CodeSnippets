def verify_fp8_support_if_applicable(model_config):
    quant_method = get_quant_type(model_config)
    if quant_method in ["fbgemm_fp8", "fp8"] and DEVICE_TYPE != "cuda":
        raise ValueError(
            f"Unsloth: FP8 quantization is only supported on CUDA GPUs. You are using {DEVICE_TYPE}."
        )

    # [TODO] Need to add FP8 support for Intel XPUs
    if DEVICE_TYPE == "cuda":
        major_version, minor_version = torch.cuda.get_device_capability()
        if quant_method == "fbgemm_fp8" and major_version < 9:
            # While L4 does support FP8 as data type, it doesn't have fbgemm (package) support yet. So we restrict it.
            raise ValueError(
                f"Unsloth: FBGEMM FP8 quantization is only supported on H100 and higher GPUs. L4 is not supported. You are using {torch.cuda.get_device_name()}. Refer to https://developer.nvidia.com/cuda-gpus for more details."
            )
        if quant_method == "fp8" and major_version * 10 + minor_version < 89:
            # In case of block quantized, we allow L4 because we fall back to torchao kernels.
            raise ValueError(
                f"Unsloth: FP8 quantization is only supported on L4 and higher GPUs with compute capability 8.9 or higher. You are using {torch.cuda.get_device_name()}. Refer to https://developer.nvidia.com/cuda-gpus for more details."
            )