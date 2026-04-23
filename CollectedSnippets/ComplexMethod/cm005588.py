def validate_environment(self, *args, **kwargs):
        if not is_torch_available():
            raise ImportError(
                "Using mxfp4 quantization requires torch"
                "Please install the latest version of torch ( pip install --upgrade torch )"
            )

        if self.quantization_config.dequantize:
            return

        if not is_accelerate_available():
            raise ImportError("Using mxfp4 requires Accelerate: `pip install accelerate`")

        device = torch.accelerator.current_accelerator() or torch.device("cpu")
        if device.type not in ["cuda", "xpu", "cpu"]:
            if self.pre_quantized:
                logger.warning_once(
                    f"Using MXFP4 quantized models requires model on cuda/xpu/cpu, but found {device}, we will default to dequantizing the model to bf16. To use mxfp4, please disable the current accelerator."
                )
                self.quantization_config.dequantize = True
                return
            else:
                raise RuntimeError(
                    f"Quantizing a model using MXFP4 requires model on cuda/xpu/cpu, but found {device}. To use mxfp4, please disable the current accelerator."
                )

        if torch.xpu.is_available():
            is_device_supported_mxfp4 = True
            triton_available = is_triton_available("3.5.0")
            kernels_installed = is_kernels_available()
        elif torch.cuda.is_available():
            compute_capability = torch.cuda.get_device_capability()
            is_device_supported_mxfp4 = compute_capability >= (7, 5)
            triton_available = is_triton_available("3.4.0")
            kernels_installed = is_kernels_available()
        elif device.type == "cpu":
            is_device_supported_mxfp4 = True
            triton_available = is_triton_available("3.5.0")
            kernels_installed = is_kernels_available()
        else:
            is_device_supported_mxfp4 = False
            triton_available = False
            kernels_installed = False

        if self.pre_quantized:
            if not is_device_supported_mxfp4:
                logger.warning_once(
                    "MXFP4 quantization is only supported on GPUs with compute capability >= 7.5 "
                    "(e.g T4, A100, L4, H100, or B200) or XPUs (e.g Intel® Data Center GPU Max Series). "
                    "We will default to dequantizing the model to bf16."
                )
                self.quantization_config.dequantize = True
                return

            if not triton_available:
                logger.warning_once(
                    "MXFP4 quantization requires Triton: CUDA requires Triton >= 3.4.0, "
                    "XPU/CPU requires Triton >= 3.5.0. Please install triton: `pip install triton`. "
                    "We will default to dequantizing the model to bf16."
                )
                self.quantization_config.dequantize = True
                return

            if not kernels_installed:
                logger.warning_once(
                    "MXFP4 quantization requires the `kernels` package: "
                    "`pip install kernels>=0.12.0`. "
                    "We will default to dequantizing the model to bf16."
                )
                self.quantization_config.dequantize = True
                return
        elif not is_device_supported_mxfp4:
            raise ValueError(
                "MXFP4 quantization is only supported on GPUs with compute capability >= 7.5 "
                "(e.g T4, A100, L4, H100, or B200) or XPUs (e.g Intel® Data Center GPU Max Series) or CPU"
            )
        elif not triton_available:
            raise ValueError(
                "MXFP4 quantization requires Triton: CUDA requires Triton >= 3.4.0, "
                "XPU/CPU requires Triton >= 3.5.0. Please install triton: `pip install triton`"
            )
        elif not kernels_installed:
            raise ValueError("MXFP4 quantization requires the `kernels` package: `pip install kernels>=0.12.0`")

        if not self.pre_quantized:
            self._lazy_import_kernels()

        device_map = kwargs.get("device_map")
        if device_map is not None and isinstance(device_map, dict):
            if not self.pre_quantized and "disk" in device_map.values():
                raise ValueError(
                    "You are attempting to load an FP4 model with a device_map that contains a disk device."
                    "This is not supported when the model is quantized on the fly. "
                    "Please use a quantized checkpoint or remove the disk device from the device_map."
                )