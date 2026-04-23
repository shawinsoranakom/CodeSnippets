def validate_environment(self, *args, **kwargs):
        if not is_accelerate_available():
            raise ImportError("Loading a BitNet quantized model requires accelerate (`pip install accelerate`)")

        if not torch.cuda.is_available():
            logger.warning_once(
                "You don't have a GPU available to load the model, the inference will be slow because of weight unpacking"
            )
            return

        device_map = kwargs.get("device_map")
        if device_map is None:
            logger.warning_once(
                "You have loaded a BitNet model on CPU and have a CUDA device available, make sure to set "
                "your model on a GPU device in order to run your model."
            )
        elif isinstance(device_map, dict):
            if len(device_map) > 1 and "cpu" in device_map.values() or "disk" in device_map.values():
                raise ValueError(
                    "You are attempting to load a BitNet model with a device_map that contains a CPU or disk device."
                    "This is not supported. Please remove the CPU or disk device from the device_map."
                )