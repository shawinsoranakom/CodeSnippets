def _skip_on_failed_cache_prerequisites(test, cache_implementation):
    """Function to skip tests on failed cache prerequisites, given a cache implementation"""
    # Installed dependencies
    if cache_implementation == "quantized" and not is_optimum_quanto_available():
        test.skipTest("Quanto is not available")
    # Devices
    if "offloaded" in cache_implementation:
        has_accelerator = torch_device is not None and torch_device != "cpu"
        if not has_accelerator:
            test.skipTest("Offloaded caches require an accelerator")
        if cache_implementation in ["offloaded_static", "offloaded_hybrid_chunked"]:
            if backend_device_count(torch_device) != 1:
                test.skipTest("Offloaded static caches require exactly 1 accelerator")