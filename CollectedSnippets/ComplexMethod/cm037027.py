def pretty_str(envinfo):
    def replace_nones(dct, replacement="Could not collect"):
        for key in dct.keys():
            if dct[key] is not None:
                continue
            dct[key] = replacement
        return dct

    def replace_bools(dct, true="Yes", false="No"):
        for key in dct.keys():
            if dct[key] is True:
                dct[key] = true
            elif dct[key] is False:
                dct[key] = false
        return dct

    def prepend(text, tag="[prepend]"):
        lines = text.split("\n")
        updated_lines = [tag + line for line in lines]
        return "\n".join(updated_lines)

    def replace_if_empty(text, replacement="No relevant packages"):
        if text is not None and len(text) == 0:
            return replacement
        return text

    def maybe_start_on_next_line(string):
        # If `string` is multiline, prepend a \n to it.
        if string is not None and len(string.split("\n")) > 1:
            return "\n{}\n".format(string)
        return string

    mutable_dict = envinfo._asdict()

    # If nvidia_gpu_models is multiline, start on the next line
    mutable_dict["nvidia_gpu_models"] = maybe_start_on_next_line(
        envinfo.nvidia_gpu_models
    )

    # If the machine doesn't have CUDA, report some fields as 'No CUDA'
    dynamic_cuda_fields = [
        "cuda_runtime_version",
        "nvidia_gpu_models",
        "nvidia_driver_version",
    ]
    all_cuda_fields = dynamic_cuda_fields + ["cudnn_version"]
    all_dynamic_cuda_fields_missing = all(
        mutable_dict[field] is None for field in dynamic_cuda_fields
    )
    if (
        TORCH_AVAILABLE
        and not torch.cuda.is_available()
        and all_dynamic_cuda_fields_missing
    ):
        for field in all_cuda_fields:
            mutable_dict[field] = "No CUDA"
        if envinfo.cuda_compiled_version is None:
            mutable_dict["cuda_compiled_version"] = "None"

    # If the machine doesn't have XPU, report XPU fields as 'No XPU'
    dynamic_xpu_fields = [
        "intel_graphics_compiler_version",
        "intel_gpu_models",
        "level_zero_loader_version",
        "level_zero_driver_version",
        "oneccl_version",
        "libigdgmm_version",
        "vllm_xpu_kernels_version",
    ]
    all_xpu_fields = dynamic_xpu_fields + [
        "oneapi_compiler_version",
        "sycl_version",
    ]
    all_dynamic_xpu_fields_missing = all(
        mutable_dict[field] is None for field in dynamic_xpu_fields
    )
    xpu_available = mutable_dict.get("xpu_available") == "True"
    if not xpu_available and all_dynamic_xpu_fields_missing:
        for field in all_xpu_fields:
            mutable_dict[field] = "No XPU"
    if envinfo.xpu_runtime_version is None or envinfo.xpu_runtime_version == "N/A":
        mutable_dict["xpu_runtime_version"] = "N/A"

    # If intel_gpu_models is multiline, start on the next line
    mutable_dict["intel_gpu_models"] = maybe_start_on_next_line(
        mutable_dict.get("intel_gpu_models")
    )

    # Replace True with Yes, False with No
    mutable_dict = replace_bools(mutable_dict)

    # Replace all None objects with 'Could not collect'
    mutable_dict = replace_nones(mutable_dict)

    # If either of these are '', replace with 'No relevant packages'
    mutable_dict["pip_packages"] = replace_if_empty(mutable_dict["pip_packages"])
    mutable_dict["conda_packages"] = replace_if_empty(mutable_dict["conda_packages"])

    # Tag conda and pip packages with a prefix
    # If they were previously None, they'll show up as ie '[conda] Could not collect'
    if mutable_dict["pip_packages"]:
        mutable_dict["pip_packages"] = prepend(
            mutable_dict["pip_packages"], "[{}] ".format(envinfo.pip_version)
        )
    if mutable_dict["conda_packages"]:
        mutable_dict["conda_packages"] = prepend(
            mutable_dict["conda_packages"], "[conda] "
        )
    mutable_dict["cpu_info"] = envinfo.cpu_info

    CUDA_FMT = """
==============================
       CUDA / GPU Info
==============================
Is CUDA available            : {is_cuda_available}
CUDA runtime version         : {cuda_runtime_version}
CUDA_MODULE_LOADING set to   : {cuda_module_loading}
GPU models and configuration : {nvidia_gpu_models}
Nvidia driver version        : {nvidia_driver_version}
cuDNN version                : {cudnn_version}
HIP runtime version          : {hip_runtime_version}
MIOpen runtime version       : {miopen_runtime_version}
Is XNNPACK available         : {is_xnnpack_available}
""".strip()

    XPU_FMT = """
==============================
      Intel XPU / GPU Info
==============================
Is XPU available             : {xpu_available}
XPU runtime version          : {xpu_runtime_version}
Intel GPU models             : {intel_gpu_models}

--Compile time--
oneAPI compiler version      : {oneapi_compiler_version}
SYCL compiler build          : {sycl_version}
oneCCL version               : {oneccl_version}

--Runtime--
Intel Graphics Compiler (IGC): {intel_graphics_compiler_version}
Intel GMM (libigdgmm)        : {libigdgmm_version}
Level Zero loader version    : {level_zero_loader_version}
Level Zero driver version    : {level_zero_driver_version}
vLLM XPU kernels version     : {vllm_xpu_kernels_version}
""".strip()

    invalid_vers = {"N/A", "Could not collect", "None"}
    sections = []

    if (
        mutable_dict.get("is_cuda_available") in ("True", "Yes")
        or mutable_dict.get("cuda_compiled_version") not in invalid_vers
    ):
        sections.append(CUDA_FMT)

    if (
        mutable_dict.get("xpu_available") in ("True", "Yes")
        or mutable_dict.get("xpu_runtime_version") not in invalid_vers
    ):
        sections.append(XPU_FMT)

    mutable_dict["gpu_info"] = (
        ("\n\n".join(sections) + "\n").format(**mutable_dict) if sections else ""
    )

    return env_info_fmt.format(**mutable_dict)