def validate_environment(self, *args, **kwargs):
        if not is_optimum_quanto_available():
            raise ImportError(
                "Loading an optimum-quanto quantized model requires optimum-quanto library (`pip install optimum-quanto`)"
            )
        if not is_accelerate_available():
            raise ImportError(
                "Loading an optimum-quanto quantized model requires accelerate library (`pip install accelerate`)"
            )
        device_map = kwargs.get("device_map")
        if isinstance(device_map, dict):
            if len(device_map) > 1 and "cpu" in device_map.values() or "disk" in device_map.values():
                raise ValueError(
                    "You are attempting to load an model with a device_map that contains a CPU or disk device."
                    "This is not supported with quanto when the model is quantized on the fly. "
                    "Please remove the CPU or disk device from the device_map."
                )
        if self.quantization_config.activations is not None:
            raise ValueError(
                "We don't support quantizing the activations with transformers library."
                "Use quanto library for more complex use cases such as activations quantization, calibration and quantization aware training."
            )