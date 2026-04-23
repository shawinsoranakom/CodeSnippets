def select_device(device="", newline=False, verbose=True):
    """Select the appropriate PyTorch device based on the provided arguments.

    The function takes a string specifying the device or a torch.device object and returns a torch.device object
    representing the selected device. The function also validates the number of available devices and raises an
    exception if the requested device(s) are not available.

    Args:
        device (str | torch.device, optional): Device string or torch.device object. Options include 'cpu', 'cuda', '0',
            '0,1,2,3', 'mps', 'npu', 'npu:0', or '-1' for auto-select. Defaults to auto-selecting the first available
            GPU, or CPU if no GPU is available.
        newline (bool, optional): If True, adds a newline at the end of the log string.
        verbose (bool, optional): If True, logs the device information.

    Returns:
        (torch.device): Selected device.

    Examples:
        >>> select_device("cuda:0")
        device(type='cuda', index=0)

        >>> select_device("cpu")
        device(type='cpu')

    Notes:
        Sets the 'CUDA_VISIBLE_DEVICES' environment variable for specifying which GPUs to use.
    """
    if isinstance(device, torch.device) or str(device).startswith(("tpu", "intel", "vulkan")):
        return device

    s = f"Ultralytics {__version__} 🚀 Python-{PYTHON_VERSION} torch-{TORCH_VERSION} "
    device = str(device).lower()
    for remove in "cuda:", "none", "(", ")", "[", "]", "'", " ":
        device = device.replace(remove, "")  # to string, 'cuda:0' -> '0' and '(0, 1)' -> '0,1'

    # Huawei Ascend NPU
    if device.startswith("npu"):
        try:
            import torch_npu  # noqa
        except ImportError:
            raise ValueError(f"Invalid NPU 'device={device}'. Install 'torch_npu' at https://github.com/Ascend/pytorch")

        if not hasattr(torch, "npu") or not torch.npu.is_available():
            raise ValueError(f"Invalid NPU 'device={device}' requested. Ascend NPU is not available.")

        # Parse 'npu' or 'npu:N' (multi-NPU not yet supported)
        suffix = device[3:]
        if suffix == "":
            idx = 0
        elif suffix.startswith(":") and suffix[1:].isdigit():
            idx = int(suffix[1:])
        else:
            raise ValueError(f"Invalid NPU 'device={device}' format. Use 'npu' or 'npu:0'.")

        n = torch.npu.device_count()
        if idx >= n:
            raise ValueError(f"Invalid NPU 'device={device}' requested. Only {n} NPU(s) available.")

        torch.npu.set_device(idx)
        if verbose:
            LOGGER.info(f"{s}NPU:{idx} ({torch.npu.get_device_name(idx)})\n")
        return torch.device(f"npu:{idx}")

    # Auto-select GPUs
    if "-1" in device:
        from ultralytics.utils.autodevice import GPUInfo

        # Replace each -1 with a selected GPU or remove it
        parts = device.split(",")
        selected = GPUInfo().select_idle_gpu(count=parts.count("-1"), min_memory_fraction=0.2)
        for i in range(len(parts)):
            if parts[i] == "-1":
                parts[i] = str(selected.pop(0)) if selected else ""
        device = ",".join(p for p in parts if p)

    cpu = device == "cpu"
    mps = device in {"mps", "mps:0"}  # Apple Metal Performance Shaders (MPS)
    if cpu or mps:
        os.environ["CUDA_VISIBLE_DEVICES"] = ""  # force torch.cuda.is_available() = False
    elif device:  # non-cpu device requested
        if device == "cuda":
            device = "0"
        if "," in device:
            device = ",".join([x for x in device.split(",") if x])  # remove sequential commas, i.e. "0,,1" -> "0,1"
        visible = os.environ.get("CUDA_VISIBLE_DEVICES", None)
        os.environ["CUDA_VISIBLE_DEVICES"] = device  # set environment variable - must be before assert is_available()
        if not (torch.cuda.is_available() and torch.cuda.device_count() >= len(device.split(","))):
            LOGGER.info(s)
            install = (
                "See https://pytorch.org/get-started/locally/ for up-to-date torch install instructions if no "
                "CUDA devices are seen by torch.\n"
                if torch.cuda.device_count() == 0
                else ""
            )
            raise ValueError(
                f"Invalid CUDA 'device={device}' requested."
                f" Use 'device=cpu' or pass valid CUDA device(s) if available,"
                f" i.e. 'device=0' or 'device=0,1,2,3' for Multi-GPU.\n"
                f"\ntorch.cuda.is_available(): {torch.cuda.is_available()}"
                f"\ntorch.cuda.device_count(): {torch.cuda.device_count()}"
                f"\nos.environ['CUDA_VISIBLE_DEVICES']: {visible}\n"
                f"{install}"
            )

    if not cpu and not mps and torch.cuda.is_available():  # prefer GPU if available
        devices = device.split(",") if device else "0"  # i.e. "0,1" -> ["0", "1"]
        space = " " * len(s)
        for i, d in enumerate(devices):
            s += f"{'' if i == 0 else space}CUDA:{d} ({get_gpu_info(i)})\n"  # bytes to MB
        arg = "cuda:0"
    elif mps and TORCH_2_0 and torch.backends.mps.is_available():
        # Prefer MPS if available
        s += f"MPS ({get_cpu_info()})\n"
        arg = "mps"
    else:  # revert to CPU
        s += f"CPU ({get_cpu_info()})\n"
        arg = "cpu"

    if arg in {"cpu", "mps"}:
        torch.set_num_threads(NUM_THREADS)  # reset OMP_NUM_THREADS for cpu training
    if verbose:
        LOGGER.info(s if newline else s.rstrip())
    return torch.device(arg)