def check_vllm_torch_sm100_compatibility():
    """
    Check for incompatible vLLM + torch < 2.9.0 + SM100 (Blackwell) combination.

    vLLM's distributed module (device_communicators) crashes with std::bad_alloc
    when imported on SM100 GPUs (B200/B100) with torch < 2.9.0. This is due to
    C++ code in vLLM's NCCL/distributed layer being incompatible with older
    torch versions on the newer Blackwell architecture.

    This check runs early (before vLLM import) to provide a helpful error message
    instead of a cryptic std::bad_alloc crash.
    """
    # Check if vLLM is installed (without importing it)
    if importlib.util.find_spec("vllm") is None:
        return

    # Check torch version
    try:
        torch_version = Version(importlib_version("torch"))
        if torch_version >= Version("2.9.0"):
            return  # torch >= 2.9.0 is compatible
    except Exception:
        return  # Can't determine torch version, skip check

    # Check if any CUDA GPU is SM100 (Blackwell)
    try:
        import torch

        if not torch.cuda.is_available():
            return

        has_sm100 = False
        sm100_gpu_name = None
        for i in range(torch.cuda.device_count()):
            major, minor = torch.cuda.get_device_capability(i)
            if major == 10:
                has_sm100 = True
                sm100_gpu_name = torch.cuda.get_device_name(i)
                break

        if not has_sm100:
            return
    except Exception:
        return

    # Get vLLM version for the error message
    try:
        vllm_version = importlib_version("vllm")
    except Exception:
        vllm_version = "unknown"

    # Incompatible combination detected - raise helpful error
    raise RuntimeError(
        f"Unsloth: Incompatible configuration detected.\n\n"
        f"  GPU: {sm100_gpu_name} (SM100 / Blackwell architecture)\n"
        f"  torch version: {torch_version}\n"
        f"  vLLM version: {vllm_version}\n\n"
        f"vLLM's distributed module crashes with std::bad_alloc on SM100 GPUs "
        f"(B200/B100/Blackwell) when using torch < 2.9.0.\n\n"
        f"To fix this, please upgrade torch:\n"
        f"  pip install --upgrade torch>=2.9.0\n\n"
        f"Alternatively, if you don't need vLLM:\n"
        f"  pip uninstall vllm"
    )