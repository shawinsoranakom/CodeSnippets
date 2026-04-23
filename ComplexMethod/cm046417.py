def _get_environment_info():
    """Collect comprehensive environment info using existing ultralytics utilities."""
    import shutil

    import psutil
    import torch

    from ultralytics import __version__
    from ultralytics.utils.torch_utils import get_cpu_info, get_gpu_info

    # Get RAM and disk totals
    memory = psutil.virtual_memory()
    disk_usage = shutil.disk_usage("/")

    env = {
        "ultralyticsVersion": __version__,
        "hostname": socket.gethostname(),
        "os": platform.platform(),
        "environment": ENVIRONMENT,
        "pythonVersion": PYTHON_VERSION,
        "pythonExecutable": sys.executable,
        "cpuCount": os.cpu_count() or 0,
        "cpu": get_cpu_info(),
        "command": " ".join(sys.argv),
        "totalRamGb": round(memory.total / (1 << 30), 1),  # Total RAM in GB
        "totalDiskGb": round(disk_usage.total / (1 << 30), 1),  # Total disk in GB
    }

    # Git info using cached GIT singleton (no subprocess calls)
    try:
        if GIT.is_repo:
            if GIT.origin:
                env["gitRepository"] = GIT.origin
            if GIT.branch:
                env["gitBranch"] = GIT.branch
            if GIT.commit:
                env["gitCommit"] = GIT.commit[:12]  # Short hash
    except Exception:
        pass

    # GPU info
    try:
        if torch.cuda.is_available():
            env["gpuCount"] = torch.cuda.device_count()
            env["gpuType"] = get_gpu_info(0) if torch.cuda.device_count() > 0 else None
    except Exception:
        pass

    return env