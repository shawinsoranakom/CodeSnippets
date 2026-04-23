def get_device_type():
    if hasattr(torch, "cuda") and torch.cuda.is_available():
        if is_hip():
            return "hip"
        return "cuda"
    elif hasattr(torch, "xpu") and torch.xpu.is_available():
        return "xpu"
    # Check torch.accelerator
    if hasattr(torch, "accelerator"):
        if not torch.accelerator.is_available():
            raise NotImplementedError(
                "Unsloth cannot find any torch accelerator? You need a GPU."
            )
        accelerator = str(torch.accelerator.current_accelerator())
        if accelerator in ("cuda", "xpu", "hip"):
            raise RuntimeError(
                f"Unsloth: Weirdly `torch.cuda.is_available()`, `torch.xpu.is_available()` and `is_hip` all failed.\n"
                f"But `torch.accelerator.current_accelerator()` works with it being = `{accelerator}`\n"
                f"Please reinstall torch - it's most likely broken :("
            )
    raise NotImplementedError(
        "Unsloth currently only works on NVIDIA, AMD and Intel GPUs."
    )