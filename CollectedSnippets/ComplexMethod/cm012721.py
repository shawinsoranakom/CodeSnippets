def _nvcc_arch_as_compile_option() -> str:
    arch = cuda_env.get_cuda_arch()
    if arch == "90":
        # Required by cutlass compilation.
        return "90a"
    if arch == "100":
        return "100a"
    if arch == "101":
        return "101a"
    if arch == "103":
        return "103a"
    if arch == "110":
        return "110a"
    if arch == "120":
        return "120a"
    if arch == "121":
        return "121a"
    return arch