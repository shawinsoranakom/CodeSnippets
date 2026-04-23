def __init__(
        self,
        module: T,
        device_ids: Sequence[int | torch.device] | None = None,
        output_device: int | torch.device | None = None,
        dim: int = 0,
    ) -> None:
        super().__init__()
        torch._C._log_api_usage_once("torch.nn.parallel.DataParallel")
        device_type = _get_available_device_type()
        if device_type is None or device_type == "mps":
            self.module = module
            self.device_ids = []
            return

        if device_ids is None:
            device_ids = _get_all_device_indices()

        if device_ids is None:
            raise RuntimeError("no available devices were found")

        if output_device is None:
            output_device = device_ids[0]

        self.dim = dim
        self.module = module
        self.device_ids = [_get_device_index(x, True) for x in device_ids]
        self.output_device = _get_device_index(output_device, True)
        self.src_device_obj = torch.device(device_type, self.device_ids[0])

        if device_type == "cuda":
            _check_balance(self.device_ids)

        if len(self.device_ids) == 1:
            self.module.to(self.src_device_obj)