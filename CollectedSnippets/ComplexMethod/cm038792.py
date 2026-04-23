def _is_auto_numa_available() -> bool:
    """Check whether automatic GPU-to-NUMA detection should be attempted."""
    from vllm.platforms import current_platform

    if not current_platform.is_cuda_alike():
        return False

    if not os.path.isdir("/sys/devices/system/node/node1"):
        return False

    try:
        process = psutil.Process(os.getpid())
        cpu_affinity = process.cpu_affinity()
        cpu_count = psutil.cpu_count()
        if cpu_count is not None and cpu_affinity != list(range(cpu_count)):
            logger.warning(
                "CPU affinity is already constrained for this process. "
                "Skipping automatic NUMA binding; pass --numa-bind-nodes "
                "explicitly to override."
            )
            return False
    except (AttributeError, NotImplementedError, psutil.Error):
        pass

    if not _can_set_mempolicy():
        logger.warning(
            "User lacks permission to set NUMA memory policy. "
            "Automatic NUMA detection may not work; if you are using Docker, "
            "try adding --cap-add SYS_NICE."
        )
        return False

    if not hasattr(current_platform, "get_all_device_numa_nodes"):
        logger.warning(
            "Platform %s does not support automatic NUMA detection",
            type(current_platform).__name__,
        )
        return False

    return True