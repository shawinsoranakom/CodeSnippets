def device_count() -> int:
    r"""
    Return the number of GPUs available.

    .. note:: This API will NOT poison fork if NVML discovery succeeds.
        See :ref:`multiprocessing-poison-fork-note` for more details.
    """
    global _cached_device_count
    if not _is_compiled():
        return 0
    if _cached_device_count is not None:
        return _cached_device_count
    if _initialized or hasattr(_tls, "is_initializing"):
        r = torch._C._cuda_getDeviceCount()
    else:
        # bypass _device_count_nvml() if rocm (not supported)
        if torch.version.hip:
            nvml_count = _device_count_amdsmi()
        else:
            nvml_count = _device_count_nvml()
        r = torch._C._cuda_getDeviceCount() if nvml_count < 0 else nvml_count
    # NB: Do not cache the device count prior to CUDA initialization, because
    # the number of devices can change due to changes to CUDA_VISIBLE_DEVICES
    # setting prior to CUDA initialization.
    if _initialized:
        _cached_device_count = r
    return r