def __init__(self, sample_interval_sec: float = 0.05, logger: Logger | None = None):
        self.sample_interval_sec = sample_interval_sec
        self.logger = logger if logger is not None else _logger
        self.gpu_type = None
        self.process = None

        device_type = torch.accelerator.current_accelerator().type if is_torch_accelerator_available() else "cuda"
        torch_accelerator_module = getattr(torch, device_type, torch.cuda)
        self.num_available_gpus = torch_accelerator_module.device_count()
        if self.num_available_gpus == 0:
            self.logger.warning(f"No GPUs detected by torch.{device_type}.device_count().")
            return

        # Determine GPU type
        device_name, _ = get_device_name_and_memory_total()
        if "amd" in device_name.lower():
            self.gpu_type = "amd"
        elif "nvidia" in device_name.lower():
            self.gpu_type = "nvidia"
        elif "intel" in device_name.lower() or device_type == "xpu":
            self.gpu_type = "intel"
        else:
            self.logger.warning(f"Unsupported GPU for monitoring: {device_name}")