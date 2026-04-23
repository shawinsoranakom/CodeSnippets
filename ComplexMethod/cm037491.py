def cpu_platform_plugin() -> str | None:
    is_cpu = False
    logger.debug("Checking if CPU platform is available.")
    try:
        is_cpu = vllm_version_matches_substr("cpu")
        if is_cpu:
            logger.debug(
                "Confirmed CPU platform is available because vLLM is built with CPU."
            )
        if not is_cpu:
            import sys

            is_cpu = sys.platform.startswith("darwin")
            if is_cpu:
                logger.debug(
                    "Confirmed CPU platform is available because the machine is MacOS."
                )

    except Exception as e:
        logger.debug("CPU platform is not available because: %s", str(e))

    if not is_cpu:
        return None

    if _is_amd_zen_cpu():
        try:
            import zentorch  # noqa: F401

            logger.debug(
                "AMD Zen CPU detected with zentorch installed, using ZenCpuPlatform."
            )
            return "vllm.platforms.zen_cpu.ZenCpuPlatform"
        except ImportError:
            logger.debug(
                "AMD Zen CPU detected but zentorch not installed, "
                "falling back to CpuPlatform."
            )

    return "vllm.platforms.cpu.CpuPlatform"