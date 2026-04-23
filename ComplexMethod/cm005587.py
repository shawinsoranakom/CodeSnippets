def validate_environment(self, *args, **kwargs):
        if not is_torch_cuda_available() and not is_torch_xpu_available():
            raise ImportError("Using fbgemm fp8 quantization requires a GPU or XPU")
        if is_torch_xpu_available() and not is_kernels_available():
            raise ImportError("Using FP8 fbgemm on XPU requires kernels (`pip install kernels`)")
        if is_torch_cuda_available() and not is_fbgemm_gpu_available():
            raise ImportError(
                "Loading an FP8 fbgemm quantized model on CUDA requires fbgemm-gpu library"
                "Please install the latest version of fbgemm-gpu library by following : https://pytorch.org/FBGEMM/fbgemm_gpu-development/InstallationInstructions.html#fbgemm-gpu-install-libraries"
            )
        if not is_accelerate_available():
            raise ImportError(
                "Loading an FP8 quantized model requires accelerate (`pip install --upgrade accelerate`)"
            )
        if is_torch_cuda_available():
            compute_capability = torch.cuda.get_device_capability()
            major, _ = compute_capability
            if major < 9:
                raise ValueError(
                    "FP8 quantized models is only supported on GPUs with compute capability >= 9.0 (e.g H100)"
                )

        device_map = kwargs.get("device_map")
        if device_map is None:
            logger.warning_once(
                "You have loaded an FP8 model on CPU and have a CUDA/XPU device available, make sure to set "
                "your model on a GPU/XPU device in order to run your model. To remove this warning, pass device_map = 'cuda' or 'xpu' or 'auto'. "
            )
        elif isinstance(device_map, dict):
            if not self.pre_quantized and ("cpu" in device_map.values() or "disk" in device_map.values()):
                raise ValueError(
                    "You are attempting to load an FP8 model with a device_map that contains a CPU or disk device."
                    "This is not supported when the model is quantized on the fly. "
                    "Please use a quantized checkpoint or remove the CPU or disk device from the device_map."
                )