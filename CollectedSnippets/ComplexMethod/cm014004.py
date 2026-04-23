def _cuda_system_info_comment() -> str:
    if not torch.cuda.is_available():
        return "# torch.cuda.is_available()==False, no GPU info collected\n"

    model_str = "# CUDA Info: \n"
    try:
        if torch.version.hip is None:
            cuda_version_out = subprocess.check_output(["nvcc", "--version"])
            cuda_version_lines = cuda_version_out.decode().split("\n")
            comment = "".join([f"# {s} \n" for s in cuda_version_lines if s != ""])
            model_str += f"{comment}\n"
        else:
            model_str += "# Not searching for nvcc on ROCM setup\n"
    except (FileNotFoundError, subprocess.CalledProcessError):
        model_str += "# nvcc not found\n"

    gpu_names = Counter(
        torch.cuda.get_device_name(i) for i in range(torch.cuda.device_count())
    )

    model_str += "# GPU Hardware Info: \n"
    for name, count in gpu_names.items():
        model_str += f"# {name} : {count} \n"
    model_str += "\n"
    return model_str