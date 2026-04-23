def validate_environment(self, device_map, **kwargs):
        if not torch.cuda.is_available():
            raise NotImplementedError("HIGGS quantization is only supported on GPU. Please use a different quantizer.")

        if not is_accelerate_available():
            raise ImportError("Using `higgs` quantization requires Accelerate: `pip install accelerate`")

        if not is_flute_available():
            raise ImportError("Using `higgs` quantization requires FLUTE: `pip install flute-kernel>=0.3.0`")

        if not is_hadamard_available():
            raise ImportError(
                "Using `higgs` quantization requires fast_hadamard_transform: `pip install fast_hadamard_transform`"
            )

        if device_map is None:
            raise ValueError(
                "You are attempting to load a HIGGS model without setting device_map."
                " Please set device_map comprised of 'cuda' devices."
            )
        elif isinstance(device_map, dict):
            if "cpu" in device_map.values() or "disk" in device_map.values():
                raise ValueError(
                    "You are attempting to load a HIGGS model with a device_map that contains a CPU or disk device."
                    " This is not supported. Please remove the CPU or disk device from the device_map."
                )