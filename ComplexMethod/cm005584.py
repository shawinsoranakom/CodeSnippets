def validate_environment(self, device_map, **kwargs):
        if not torch.cuda.is_available() and not is_torch_xpu_available():
            raise NotImplementedError(
                "FPQuant quantization is only supported on GPU or Intel XPU. Please use a different quantizer."
            )

        if not is_qutlass_available() and not self.quantization_config.pseudoquantization:
            raise ImportError(
                "Using `fp_quant` with real quantization requires a **Blackwell GPU** and qutlass: `git clone https://github.com/IST-DASLab/qutlass.git && cd qutlass && pip install --no-build-isolation .`. You can use `FPQuantConfig(pseudoquantization=True, ...)` to use Triton-based pseudo-quantization. It doesn't provide any speedups but emulates the quantization behavior of the real quantization."
            )

        if (
            self.quantization_config.pseudoquantization
            and self.quantization_config.forward_dtype == "nvfp4"
            and torch.cuda.is_available()
            and torch.cuda.get_device_capability()[0] < 9
        ):
            raise ValueError(
                "NVFP4 pseudoquantization requires a GPU with compute capability >= 9.0 (Hopper or newer) "
                "because the Triton kernel uses the `fp8e4nv` type. Please use `forward_dtype='mxfp4'` instead, "
                "or use a GPU with compute capability >= 9.0."
            )

        if self.quantization_config.pseudoquantization:
            logger.warning(
                "Using pseudo-quantization for FP-Quant. This doesn't provide any speedups but emulates the quantization behavior of the real quantization."
            )

        if not is_fp_quant_available():
            raise ImportError("Using `fp_quant` quantization requires fp_quant: `pip install fp_quant`")

        if device_map is None and not self.quantization_config.pseudoquantization:
            raise ValueError(
                "You are attempting to load a FPQuant model without setting device_map."
                " Please set device_map comprised of 'cuda' devices."
            )
        elif isinstance(device_map, dict):
            if (
                not self.quantization_config.pseudoquantization
                and len(device_map) > 1
                and "cpu" in device_map.values()
                or "disk" in device_map.values()
            ):
                raise ValueError(
                    "You are attempting to load a FPQuant model with a device_map that contains a CPU or disk device."
                    " This is not supported. Please remove the CPU or disk device from the device_map."
                )