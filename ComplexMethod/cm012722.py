def cuda_compile_command(
    src_files: list[str],
    dst_file: str,
    dst_file_ext: str,
    extra_args: list[str] | None = None,
) -> str:
    if extra_args is None:
        extra_args = []
    if use_re_build():
        build_path = os.path.dirname(dst_file)
        include_paths = _clone_cutlass_paths(build_path)
        src_files = [os.path.basename(src_file) for src_file in src_files]
        dst_file = os.path.basename(dst_file)
    else:
        include_paths = _cutlass_include_paths()
    cuda_lib_options = _cuda_lib_options()
    nvcc_host_compiler_options = _nvcc_host_compiler_options()
    nvcc_compiler_options = _nvcc_compiler_options()
    options = (
        nvcc_compiler_options
        + extra_args
        + [
            f"-Xcompiler {opt}" if "=" in opt else f"-Xcompiler={opt}"
            for opt in nvcc_host_compiler_options
        ]
        + ["-I" + path for path in include_paths]
        + cuda_lib_options
    )
    src_file = " ".join(src_files)
    res = ""
    if dst_file_ext == "o":
        res = f"{_cuda_compiler()} {' '.join(options)} -c -o {dst_file} {src_file}"
    elif dst_file_ext == "so":
        options.append("-shared")
        res = f"{_cuda_compiler()} {' '.join(options)} -o {dst_file} {src_file}"
    elif dst_file_ext == "exe":
        res = f"{_cuda_compiler()} {' '.join(options)} -o {dst_file} {src_file}"
    else:
        raise NotImplementedError(f"Unsupported output file suffix {dst_file_ext}!")
    if log.isEnabledFor(logging.DEBUG):
        log.debug("CUDA command: %s", res)
    else:
        autotuning_log.debug("CUDA command: %s", res)
    return res