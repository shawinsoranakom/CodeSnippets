def parse(
        self,
        model: str | Path,
        trust_remote_code: bool,
        revision: str | None = None,
        code_revision: str | None = None,
        **kwargs,
    ) -> tuple[dict, PretrainedConfig]:
        # This function loads a params.json config which
        # should be used when loading models in mistral format
        config_dict = _download_mistral_config_file(model, revision)
        if (
            max_position_embeddings := config_dict.get("max_position_embeddings")
        ) is None:
            max_position_embeddings = _maybe_retrieve_max_pos_from_hf(
                model, revision, **kwargs
            )
            config_dict["max_position_embeddings"] = max_position_embeddings

        from vllm.transformers_utils.configs.mistral import adapt_config_dict

        # Get missing fields from HF config if available
        try:
            hf_config_dict, _ = PretrainedConfig.get_config_dict(
                model,
                revision=revision,
                code_revision=code_revision,
                **without_trust_remote_code(kwargs),
            )
        except OSError:  # Not found
            hf_config_dict = {}

        if config_dict.get("dtype") is None:
            with _mistral_patch_hf_hub_constants():
                model_str = model if isinstance(model, str) else model.as_posix()
                param_mt = get_safetensors_params_metadata(model_str, revision=revision)
            if param_mt:
                param_dtypes: set[torch.dtype] = {
                    _SAFETENSORS_TO_TORCH_DTYPE[dtype]
                    for info in param_mt.values()
                    if (dtype := info.get("dtype", None))
                    and dtype in _SAFETENSORS_TO_TORCH_DTYPE
                }

                if param_dtypes:
                    config_dict["dtype"] = common_broadcastable_dtype(param_dtypes)
                    logger.info_once(
                        "Inferred from consolidated*.safetensors files "
                        f"{config_dict['dtype']} dtype."
                    )

        config = adapt_config_dict(config_dict, defaults=hf_config_dict)

        return config_dict, config