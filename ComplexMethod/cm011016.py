def __init__(self, backend: Backend):
        """Init."""
        self.device_backend_map: dict[str, Backend] = {}
        # pyrefly: ignore [bad-assignment]
        backend = str(backend)

        if backend == Backend.UNDEFINED:
            # Detect the accelerator on the machine. If no accelerator is
            # available, it returns CPU.
            device_type = torch._C._get_accelerator().type
            try:
                backend_str = Backend.default_device_backend_map[device_type]
                self.device_backend_map[device_type] = Backend(backend_str)
            except KeyError:
                raise ValueError(
                    f"We detected accelerator {device_type} on your machine. "
                    f"But we don't know which communication backend to use for this accelerator. "
                    f"Please specify the `backend` argument in the `init_process_group` call."
                ) from None
        elif backend.lower() in Backend.backend_list:
            # Cases for when backend is a single string (without device types)
            # e.g. "nccl", "gloo", "ucc", "mpi"
            supported_devices = Backend.backend_capability[backend.lower()]
            backend_val = Backend(backend)

            self.device_backend_map = dict.fromkeys(supported_devices, backend_val)
        elif ":" in backend.lower():
            # Backend specified in "device:backend" format
            # make sure the backend string is in the correct format
            # "{device_type1}:{backend1},{device_type2}:{backend2}"
            # e.g. "cpu:gloo,cuda:nccl"
            backend_str_error_message = f"""The custom backend string argument is invalid: {backend}.
                Custom backend string is an experimental feature where the backend string must be in the format:
                "<device_type1>:<backend1>,<device_type2>:<backend2>...". e.g. 'cpu:gloo,cuda:nccl'"""

            # parse the backend string and populate the device_backend_map
            for device_backend_pair_str in backend.lower().split(","):
                device_backend_pair = device_backend_pair_str.split(":")
                if len(device_backend_pair) != 2:
                    raise ValueError(
                        f"Invalid device:backend pairing: \
                                     {device_backend_pair_str}. {backend_str_error_message}"
                    )
                # pyrefly: ignore [bad-assignment]
                device, backend = device_backend_pair
                if device in self.device_backend_map:
                    raise ValueError(
                        f"Duplicate device type {device} \
                                     in backend string: {backend}. {backend_str_error_message}"
                    )
                self.device_backend_map[device] = Backend(backend)
        else:
            # User specified a single backend name whose device capability is
            # unknown, assuming it can support the default devices of PyTorch
            # (cpu and cuda)
            warnings.warn(
                f"Device capability of {backend} unknown, assuming `cpu` and "
                "`cuda`. You can specify it in `device:backend` format in "
                "`init_process_group` call.",
                stacklevel=2,
            )
            backend_val = Backend(backend)
            self.device_backend_map = {
                "cpu": backend_val,
                "cuda": backend_val,
                "xpu": backend_val,
            }

        logger.info("Using backend config: %s", self.device_backend_map)