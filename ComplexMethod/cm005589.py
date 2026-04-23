def validate_environment(self, *args, **kwargs):
        if self.quantization_config.dequantize:
            return

        if not torch.backends.mps.is_available():
            if self.pre_quantized:
                logger.warning_once(
                    "Metal quantization requires an Apple Silicon GPU (MPS), but none is available. "
                    "We will default to dequantizing the model to the original dtype."
                )
                self.quantization_config.dequantize = True
                return
            else:
                raise RuntimeError("Metal quantization requires an Apple Silicon GPU (MPS). No MPS device found.")

        if not is_kernels_available():
            raise ImportError("Metal quantization requires kernels: `pip install kernels`")

        device_map = kwargs.get("device_map")
        if device_map is None:
            logger.warning_once(
                "You have loaded a Metal quantized model on CPU and have an MPS device available. "
                "Set device_map='mps' to use the Metal kernels."
            )
        elif isinstance(device_map, dict):
            if not self.pre_quantized and ("cpu" in device_map.values() or "disk" in device_map.values()):
                raise ValueError(
                    "Metal quantization on the fly does not support CPU or disk in the device_map. "
                    "Please use a pre-quantized checkpoint or remove CPU/disk from device_map."
                )