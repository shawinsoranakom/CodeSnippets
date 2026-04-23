def _get_vllm_cuda_mismatch_message(error):
    """If the error is a CUDA version mismatch, return a helpful install message."""
    import re as _re

    checked = set()
    current = error
    wanted_cuda = None
    while current is not None and id(current) not in checked:
        checked.add(id(current))
        message = str(current)
        # Extract the CUDA version vllm was built for, e.g. "libcudart.so.12"
        match = _re.search(r"libcudart\.so\.(\d+)", message)
        if match:
            wanted_cuda = match.group(1)
            break
        current = getattr(current, "__cause__", None) or getattr(
            current, "__context__", None
        )
    if wanted_cuda is None:
        return None

    # Detect what CUDA version is actually available on the system
    system_cuda_display = None  # Human-readable, e.g. "13.0"
    system_cuda_tag = None  # For wheel URL, e.g. "130"
    try:
        import torch

        cuda_version = torch.version.cuda  # e.g. "13.0" or "12.8"
        if cuda_version:
            system_cuda_display = cuda_version
            system_cuda_tag = cuda_version.replace(".", "")[:3]  # "130" or "128"
    except Exception:
        pass

    if system_cuda_tag is None or system_cuda_tag.startswith(wanted_cuda):
        return None  # Not a mismatch or can't determine

    try:
        vllm_version = importlib_version("vllm").split("+")[0]
    except Exception:
        vllm_version = "VLLM_VERSION"

    cpu_arch = "x86_64"
    try:
        import platform

        cpu_arch = platform.machine()
    except Exception:
        pass

    return (
        f"Unsloth: vLLM was built for CUDA {wanted_cuda} but this system has "
        f"CUDA {system_cuda_display}. Please reinstall vLLM with the correct CUDA version:\n"
        f"\n"
        f"  uv pip install https://github.com/vllm-project/vllm/releases/download/"
        f"v{vllm_version}/vllm-{vllm_version}+cu{system_cuda_tag}-cp38-abi3-"
        f"manylinux_2_35_{cpu_arch}.whl"
    )