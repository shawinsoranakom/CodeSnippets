def unet_dtype(device=None, model_params=0, supported_dtypes=[torch.float16, torch.bfloat16, torch.float32], weight_dtype=None):
    if model_params < 0:
        model_params = 1000000000000000000000
    if args.fp32_unet:
        return torch.float32
    if args.fp64_unet:
        return torch.float64
    if args.bf16_unet:
        return torch.bfloat16
    if args.fp16_unet:
        return torch.float16
    if args.fp8_e4m3fn_unet:
        return torch.float8_e4m3fn
    if args.fp8_e5m2_unet:
        return torch.float8_e5m2
    if args.fp8_e8m0fnu_unet:
        return torch.float8_e8m0fnu

    fp8_dtype = None
    if weight_dtype in FLOAT8_TYPES:
        fp8_dtype = weight_dtype

    if fp8_dtype is not None:
        if supports_fp8_compute(device): #if fp8 compute is supported the casting is most likely not expensive
            return fp8_dtype

        free_model_memory = maximum_vram_for_weights(device)
        if model_params * 2 > free_model_memory:
            return fp8_dtype

    if PRIORITIZE_FP16 or weight_dtype == torch.float16:
        if torch.float16 in supported_dtypes and should_use_fp16(device=device, model_params=model_params):
            return torch.float16

    for dt in supported_dtypes:
        if dt == torch.float16 and should_use_fp16(device=device, model_params=model_params):
            if torch.float16 in supported_dtypes:
                return torch.float16
        if dt == torch.bfloat16 and should_use_bf16(device, model_params=model_params):
            if torch.bfloat16 in supported_dtypes:
                return torch.bfloat16

    for dt in supported_dtypes:
        if dt == torch.float16 and should_use_fp16(device=device, model_params=model_params, manual_cast=True):
            if torch.float16 in supported_dtypes:
                return torch.float16
        if dt == torch.bfloat16 and should_use_bf16(device, model_params=model_params, manual_cast=True):
            if torch.bfloat16 in supported_dtypes:
                return torch.bfloat16

    return torch.float32