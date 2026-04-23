def vae_dtype(device=None, allowed_dtypes=[]):
    if args.fp16_vae:
        return torch.float16
    elif args.bf16_vae:
        return torch.bfloat16
    elif args.fp32_vae:
        return torch.float32

    for d in allowed_dtypes:
        if d == torch.float16 and should_use_fp16(device):
            return d

        if d == torch.bfloat16 and should_use_bf16(device):
            return d

    return torch.float32