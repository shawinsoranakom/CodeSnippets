def generate_wheels_matrix(
    os: str,
    arches: list[str] | None = None,
    python_versions: list[str] | None = None,
) -> list[dict[str, str]]:
    package_type = "wheel"
    if os == "linux" or os == "linux-aarch64" or os == "linux-s390x":
        # NOTE: We only build manywheel packages for x86_64 and aarch64 and s390x linux
        package_type = "manywheel"

    if python_versions is None:
        python_versions = FULL_PYTHON_VERSIONS

    if arches is None:
        # Define default compute archivectures
        arches = ["cpu"]
        if os == "linux":
            arches += CUDA_ARCHES + ROCM_ARCHES + XPU_ARCHES
        elif os == "windows":
            arches += CUDA_ARCHES + XPU_ARCHES
        elif os == "linux-aarch64":
            # Separate new if as the CPU type is different and
            # uses different build/test scripts
            arches = CPU_AARCH64_ARCH + CUDA_AARCH64_ARCHES
        elif os == "linux-s390x":
            # Only want the one arch as the CPU type is different and
            # uses different build/test scripts
            arches = ["cpu-s390x"]

    ret: list[dict[str, str]] = []
    for python_version in python_versions:
        for arch_version in arches:
            gpu_arch_type = arch_type(arch_version)
            gpu_arch_version = (
                ""
                if arch_version == "cpu"
                or arch_version == "cpu-aarch64"
                or arch_version == "cpu-s390x"
                or arch_version == "xpu"
                else arch_version
            )

            # TODO: Enable python 3.14 for rest
            if os not in [
                "linux",
                "linux-aarch64",
                "linux-s390x",
                "macos-arm64",
                "windows",
            ] and (python_version == "3.14" or python_version == "3.14t"):
                continue

            # cuda linux wheels require PYTORCH_EXTRA_INSTALL_REQUIREMENTS to install

            if (
                arch_version in ["13.2", "13.0", "12.6"]
                and os == "linux"
                or arch_version in CUDA_AARCH64_ARCHES
            ):
                desired_cuda = translate_desired_cuda(gpu_arch_type, gpu_arch_version)
                ret.append(
                    {
                        "python_version": python_version,
                        "gpu_arch_type": gpu_arch_type,
                        "gpu_arch_version": gpu_arch_version,
                        "desired_cuda": desired_cuda,
                        "container_image": WHEEL_CONTAINER_IMAGES[arch_version].split(
                            ":"
                        )[0],
                        "container_image_tag_prefix": WHEEL_CONTAINER_IMAGES[
                            arch_version
                        ].split(":")[1],
                        "package_type": package_type,
                        "pytorch_extra_install_requirements": (
                            PYTORCH_EXTRA_INSTALL_REQUIREMENTS[
                                f"{desired_cuda[2:4]}.{desired_cuda[4:]}"  # for cuda-aarch64: cu126 -> 12.6
                            ]
                            if os == "linux-aarch64"
                            else PYTORCH_EXTRA_INSTALL_REQUIREMENTS[arch_version]
                        ),
                        "build_name": (
                            f"{package_type}-py{python_version}-{gpu_arch_type}"
                            f"{'-' if 'aarch64' in gpu_arch_type else ''}{gpu_arch_version.replace('-aarch64', '')}".replace(
                                ".", "_"
                            )
                        ),  # include special case for aarch64 build, remove the -aarch64 postfix
                    }
                )
            else:
                ret.append(
                    {
                        "python_version": python_version,
                        "gpu_arch_type": gpu_arch_type,
                        "gpu_arch_version": gpu_arch_version,
                        "desired_cuda": translate_desired_cuda(
                            gpu_arch_type, gpu_arch_version
                        ),
                        "container_image": WHEEL_CONTAINER_IMAGES[arch_version].split(
                            ":"
                        )[0],
                        "container_image_tag_prefix": WHEEL_CONTAINER_IMAGES[
                            arch_version
                        ].split(":")[1],
                        "package_type": package_type,
                        "build_name": f"{package_type}-py{python_version}-{gpu_arch_type}{gpu_arch_version}".replace(
                            ".", "_"
                        ),
                        "pytorch_extra_install_requirements": (
                            PYTORCH_EXTRA_INSTALL_REQUIREMENTS["xpu"]
                            if gpu_arch_type == "xpu"
                            else PYTORCH_EXTRA_INSTALL_REQUIREMENTS[CUDA_STABLE]
                            if gpu_arch_type == "cpu"
                            and os in ("windows", "macos-arm64")
                            else ""
                        ),
                    }
                )

    return ret