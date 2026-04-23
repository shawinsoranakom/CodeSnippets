def from_config(cls, config: dict[str, Any]) -> "ModelOptQuantConfigBase":
        # Handle both ModelOpt format and compressed-tensors style format
        if "quantization" in config:
            # Traditional ModelOpt format:
            # {"quantization": {"quant_algo": "..."}}
            quant_config = cls.get_from_keys(config, ["quantization"])
            if not isinstance(quant_config, dict):
                raise ValueError("Expected 'quantization' to be a dictionary in config")

            quant_method = quant_config.get("quant_algo")

            # Handle kv_cache_quant_algo with proper type validation
            kv_cache_quant_method = quant_config.get("kv_cache_quant_algo")

            # Handle group_size with proper type validation
            group_size_raw = quant_config.get("group_size")

            # "exclude_modules" is the key in the legacy hf_quant_config.json
            exclude_modules = quant_config.get("exclude_modules", [])
        else:
            # Compressed-tensors style format (config.json quantization_config):
            # {"quant_algo": "...", "quant_method": "modelopt"}
            quant_method = config.get("quant_algo")

            # "kv_cache_scheme" (a dict) instead of "kv_cache_quant_algo" (a string).
            kv_cache_scheme = config.get("kv_cache_scheme")
            if isinstance(kv_cache_scheme, dict) and (
                kv_cache_scheme.get("type") == "float"
                and kv_cache_scheme.get("num_bits") == 8
            ):
                kv_cache_quant_method = "FP8"
            else:
                kv_cache_quant_method = None

            # "ignore" is the key in config.json
            exclude_modules = config.get("ignore", [])
            group_size_raw = config.get("group_size")

        if not quant_method:
            raise ValueError("Missing 'quant_algo' in quantization config")

        # Normalize quant_algo for robust matching (ModelOpt may emit lowercase).
        quant_method = str(quant_method).upper()

        if kv_cache_quant_method is None:
            # No KV cache quantization, keep this branch just to have this comment
            pass
        elif not isinstance(kv_cache_quant_method, str):
            raise ValueError(
                f"kv_cache_quant_algo must be a string, got "
                f"{type(kv_cache_quant_method)}"
            )
        else:
            kv_cache_quant_method = kv_cache_quant_method.upper()

        if not isinstance(exclude_modules, list):
            raise ValueError(
                f"exclude_modules must be a list, got {type(exclude_modules)}"
            )

        if group_size_raw is None:
            group_size = None
        elif isinstance(group_size_raw, int):
            group_size = group_size_raw
        else:
            try:
                group_size = int(group_size_raw)
            except (ValueError, TypeError):
                raise ValueError(
                    f"group_size must be an integer, got {type(group_size_raw)}"
                ) from None

        if quant_method not in QUANT_ALGOS:
            raise ValueError(
                f"ModelOpt currently only supports: {QUANT_ALGOS} "
                "quantizations in vLLM. Please check the "
                "`hf_quant_config.json` file for your model's "
                "quant configuration."
            )
        return cls._from_config(
            quant_method=quant_method,
            kv_cache_quant_method=kv_cache_quant_method,
            exclude_modules=exclude_modules,
            group_size=group_size,
            original_config=config,
        )