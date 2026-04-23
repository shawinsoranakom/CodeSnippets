def list_gpu_processes(device: "Device" = None) -> str:
    r"""Return a human-readable printout of the running processes and their GPU memory use for a given device.

    This can be useful to display periodically during training, or when
    handling out-of-memory exceptions.

    Args:
        device (torch.device or int, optional): selected device. Returns
            printout for the current device, given by :func:`~torch.cuda.current_device`,
            if :attr:`device` is ``None`` (default).
    """
    if not torch.version.hip:
        try:
            import pynvml  # type: ignore[import]
        except ModuleNotFoundError:
            return "pynvml module not found, please install nvidia-ml-py"
        # pyrefly: ignore [import-error, missing-import, missing-module-attribute]
        from pynvml import NVMLError_DriverNotLoaded

        try:
            pynvml.nvmlInit()
        except NVMLError_DriverNotLoaded:
            return "cuda driver can't be loaded, is cuda enabled?"

        device = _get_nvml_device_index(device)
        handle = pynvml.nvmlDeviceGetHandleByIndex(device)
        procs = pynvml.nvmlDeviceGetComputeRunningProcesses(handle)
    else:
        try:
            import amdsmi  # type: ignore[import]
        except ModuleNotFoundError:
            return "amdsmi module not found, please install amdsmi"
        try:
            amdsmi.amdsmi_init()  # type: ignore[attr-defined]
        except amdsmi.AmdSmiException:  # type: ignore[attr-defined]
            return "amdsmi driver can't be loaded, is ROCm installed?"

        device = _get_amdsmi_device_index(device)

        try:
            handle = amdsmi.amdsmi_get_processor_handles()[device]  # type: ignore[attr-defined]
            procs = amdsmi.amdsmi_get_gpu_process_list(handle)  # type: ignore[attr-defined]
        except amdsmi.AmdSmiException:  # type: ignore[attr-defined]
            return "amdsmi cannot list processes from other users"

    lines = []
    lines.append(f"GPU:{device}")
    if len(procs) == 0:
        lines.append("no processes are running")
    for p in procs:
        if not torch.version.hip:
            mem = p.usedGpuMemory / (1024 * 1024)
            pid = p.pid
        else:
            try:
                proc_info = amdsmi.amdsmi_get_gpu_process_info(handle, p)  # type: ignore[possibly-undefined]
            except AttributeError:
                # https://github.com/ROCm/amdsmi/commit/c551c3caedbd903ba828e7fdffa5b56d475a15e7
                # is a BC-breaking change that removes amdsmi_get_gpu_process_info API from amdsmi
                proc_info = p
            mem = proc_info["memory_usage"]["vram_mem"] / (1024 * 1024)
            pid = proc_info["pid"]
        lines.append(f"process {pid:>10d} uses {mem:>12.3f} MB GPU memory")
    return "\n".join(lines)