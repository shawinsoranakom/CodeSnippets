def get_torch_dtype(
        cls,
        hf_config: PretrainedConfig,
        model_id: str,
        revision: str | None,
        config_format: str | ConfigFormat,
    ):
        # NOTE: getattr(config, "dtype", torch.float32) is not correct
        # because config.dtype can be None.
        config_dtype = getattr(hf_config, "dtype", None)

        # Fallbacks for multi-modal models if the root config
        # does not define dtype
        if config_dtype is None:
            config_dtype = getattr(hf_config.get_text_config(), "dtype", None)
        if config_dtype is None and hasattr(hf_config, "vision_config"):
            config_dtype = getattr(hf_config.vision_config, "dtype", None)
        if config_dtype is None and hasattr(hf_config, "encoder_config"):
            config_dtype = getattr(hf_config.encoder_config, "dtype", None)

        # Try to read the dtype of the weights if they are in safetensors format
        if config_dtype is None:
            param_mt = get_safetensors_params_metadata(model_id, revision=revision)

            if param_mt:
                param_dtypes: set[torch.dtype] = {
                    _SAFETENSORS_TO_TORCH_DTYPE[dtype]
                    for info in param_mt.values()
                    if (dtype := info.get("dtype", None))
                    and dtype in _SAFETENSORS_TO_TORCH_DTYPE
                }

                if param_dtypes:
                    return common_broadcastable_dtype(param_dtypes)

        if config_dtype is None:
            config_dtype = torch.float32

        return config_dtype