def get_requirements() -> list[str]:
    """Get Python package dependencies from requirements.txt."""
    requirements_dir = ROOT_DIR / "requirements"

    def _read_requirements(filename: str) -> list[str]:
        with open(requirements_dir / filename) as f:
            requirements = f.read().strip().split("\n")
        resolved_requirements = []
        for line in requirements:
            if line.startswith("-r "):
                resolved_requirements += _read_requirements(line.split()[1])
            elif (
                not line.startswith("--")
                and not line.startswith("#")
                and line.strip() != ""
            ):
                resolved_requirements.append(line)
        return resolved_requirements

    if _no_device():
        requirements = _read_requirements("common.txt")
    elif _is_cuda():
        requirements = _read_requirements("cuda.txt")
        cuda_major, cuda_minor = torch.version.cuda.split(".")
        modified_requirements = []
        for req in requirements:
            if "vllm-flash-attn" in req and cuda_major != "12":
                # vllm-flash-attn is built only for CUDA 12.x.
                # Skip for other versions.
                continue
            modified_requirements.append(req)
        requirements = modified_requirements
    elif _is_hip():
        requirements = _read_requirements("rocm.txt")
    elif _is_tpu():
        requirements = _read_requirements("tpu.txt")
    elif _is_cpu():
        requirements = _read_requirements("cpu.txt")
    elif _is_xpu():
        requirements = _read_requirements("xpu.txt")
    else:
        raise ValueError("Unsupported platform, please use CUDA, ROCm, or CPU.")
    return requirements