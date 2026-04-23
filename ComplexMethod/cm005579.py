def validate_environment(self, *args, **kwargs):
        if not is_torchao_available():
            raise ImportError("Loading an torchao quantized model requires torchao library (`pip install torchao`)")

        device_map = kwargs.get("device_map")
        self.offload_to_cpu = False
        if isinstance(device_map, dict):
            if ("disk" in device_map.values() or "cpu" in device_map.values()) and len(device_map) > 1:
                self.offload_to_cpu = "cpu" in device_map.values()
                if self.pre_quantized and "disk" in device_map.values():
                    raise ValueError(
                        "You are attempting to perform disk offload with a pre-quantized torchao model "
                        "This is not supported yet . Please remove the disk device from the device_map."
                    )