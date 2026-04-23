def _normalize_cuda_arch(arch: str) -> str:
    arch_num = arch
    if isinstance(arch, str):
        digits = "".join(ch for ch in arch if ch.isdigit())
        if not digits:
            raise ValueError(f"Unrecognized cuda arch: {arch}")
        arch_num = int(digits)
    else:
        arch_num = int(arch)

    if arch_num > 103:
        log.warning("Detected CUDA architecture > 103: %s. Please file an issue.", arch)
        return str(arch_num)
    if arch_num >= 103:
        return "103"
    if arch_num >= 100:
        return "100"
    if arch_num >= 90:
        return "90"
    if arch_num >= 80:
        return "80"
    if arch_num >= 75:
        return "75"
    if arch_num >= 70:
        return "70"
    raise NotImplementedError(f"Unsupported cuda arch: {arch}")