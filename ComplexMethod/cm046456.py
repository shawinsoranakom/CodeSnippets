def pick_windows_cuda_runtime(host: HostInfo) -> str | None:
    if not host.driver_cuda_version:
        return None
    major, minor = host.driver_cuda_version
    if major > 13 or (major == 13 and minor >= 1):
        return "13.1"
    if major > 12 or (major == 12 and minor >= 4):
        return "12.4"
    return None