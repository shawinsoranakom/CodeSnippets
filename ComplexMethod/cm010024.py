def __dlpack_device__(self) -> tuple[enum.IntEnum, int]:
        if has_torch_function_unary(self):
            return handle_torch_function(Tensor.__dlpack_device__, (self,), self)

        from torch.utils.dlpack import DLDeviceType

        device = self.device
        idx = device.index if device.index is not None else 0
        torch_device_type = device.type
        if torch_device_type == "cuda" and torch.version.hip is not None:
            device_type = DLDeviceType.kDLROCM
        elif torch_device_type == "cpu" and self.is_pinned():
            device_type = DLDeviceType.kDLCUDAHost
        elif torch_device_type == "cuda":
            device_type = DLDeviceType.kDLCUDA
        elif torch_device_type == "cpu":
            device_type = DLDeviceType.kDLCPU
        elif torch_device_type == "xpu":
            device_type = DLDeviceType.kDLOneAPI
        elif self.device.type == "privateuse1":
            device_type = DLDeviceType.kDLExtDev
        elif torch_device_type == "xla":
            import torch_xla

            if (
                len(torch_xla.real_devices()) <= 0
                or "cuda" not in torch_xla.real_devices()[0].lower()
            ):
                raise ValueError(f"Unknown device type {torch_device_type} for Dlpack")

            device_type = DLDeviceType.kDLCUDA
        elif torch_device_type == "mps":
            device_type = DLDeviceType.kDLMetal
        else:
            raise ValueError(f"Unknown device type {torch_device_type} for Dlpack")
        return (device_type, idx)