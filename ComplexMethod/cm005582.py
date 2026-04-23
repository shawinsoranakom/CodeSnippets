def validate_environment(self, *args, **kwargs):
        if not is_accelerate_available():
            raise ImportError(
                f"Using `bitsandbytes` 8-bit quantization requires accelerate: `pip install 'accelerate>={ACCELERATE_MIN_VERSION}'`"
            )
        if not is_bitsandbytes_available():
            raise ImportError(
                f"Using `bitsandbytes` 8-bit quantization requires bitsandbytes: `pip install -U bitsandbytes>={BITSANDBYTES_MIN_VERSION}`"
            )

        from ..integrations import validate_bnb_backend_availability

        validate_bnb_backend_availability(raise_exception=True)

        device_map = kwargs.get("device_map")
        if not self.quantization_config.llm_int8_enable_fp32_cpu_offload and isinstance(device_map, dict):
            values = set(device_map.values())
            if values != {"cpu"} and ("cpu" in values or "disk" in values):
                raise ValueError(
                    "Some modules are dispatched on the CPU or the disk. Make sure you have enough GPU RAM to fit the "
                    "quantized model. If you want to dispatch the model on the CPU or the disk while keeping these modules "
                    "in 32-bit, you need to set `llm_int8_enable_fp32_cpu_offload=True` and pass a custom `device_map` to "
                    "`from_pretrained`. Check "
                    "https://huggingface.co/docs/transformers/main/en/main_classes/quantization#offload-between-cpu-and-gpu "
                    "for more details. "
                )