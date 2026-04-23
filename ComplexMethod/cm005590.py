def validate_environment(self, *args, **kwargs):
        if not is_kernels_available():
            raise ImportError("Loading an EETQ quantized model requires kernels (`pip install kernels`)")

        if not is_accelerate_available():
            raise ImportError("Loading an EETQ quantized model requires accelerate (`pip install accelerate`)")

        if not torch.cuda.is_available():
            raise RuntimeError("No GPU found. A GPU is needed for quantization.")

        device_map = kwargs.get("device_map")
        if device_map is None:
            logger.warning_once(
                "You have loaded an EETQ model on CPU and have a CUDA device available, make sure to set "
                "your model on a GPU device in order to run your model."
            )
        elif isinstance(device_map, dict):
            if len(device_map) > 1 and "cpu" in device_map.values() or "disk" in device_map.values():
                raise ValueError(
                    "You are attempting to load an EETQ model with a device_map that contains a CPU or disk device."
                    " This is not supported. Please remove the CPU or disk device from the device_map."
                )