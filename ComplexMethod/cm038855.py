def get_kernels_to_autotune(requested_kernels: list[str] | None) -> list[str]:
    all_kernels = get_registered_kernels()
    if not all_kernels:
        logger.error("No Helion kernels found in registry")
        sys.exit(1)

    if not requested_kernels:
        return list(all_kernels.keys())

    if len(requested_kernels) != len(set(requested_kernels)):
        duplicates = [
            k for k in set(requested_kernels) if requested_kernels.count(k) > 1
        ]
        logger.error("Duplicate kernel names in --kernels flag: %s", duplicates)
        sys.exit(1)

    kernels_to_autotune = []
    missing_kernels = []

    for kernel_name in requested_kernels:
        if kernel_name in all_kernels:
            kernels_to_autotune.append(kernel_name)
        else:
            missing_kernels.append(kernel_name)

    if missing_kernels:
        logger.error("Kernel(s) not found: %s", missing_kernels)
        logger.error("Available kernels: %s", list(all_kernels.keys()))
        sys.exit(1)

    return kernels_to_autotune