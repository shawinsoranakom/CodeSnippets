def parse(
        self,
        model: str | Path,
        trust_remote_code: bool,
        revision: str | None = None,
        code_revision: str | None = None,
        **kwargs,
    ) -> tuple[dict, PretrainedConfig]:
        kwargs["local_files_only"] = huggingface_hub.constants.HF_HUB_OFFLINE
        trust_remote_code |= kwargs.get("trust_remote_code", False)
        kwargs = without_trust_remote_code(kwargs)
        config_dict, _ = PretrainedConfig.get_config_dict(
            model,
            revision=revision,
            code_revision=code_revision,
            **kwargs,
        )
        # Use custom model class if it's in our registry
        model_type = config_dict.get("model_type")
        if model_type is None:
            model_type = (
                "speculators"
                if config_dict.get("speculators_config") is not None
                else model_type
            )
        # Allow hf_overrides to override model_type before checking _CONFIG_REGISTRY
        if (hf_overrides := kwargs.pop("hf_overrides", None)) is not None:
            if isinstance(hf_overrides, dict) and "model_type" in hf_overrides:
                model_type = hf_overrides["model_type"]
            elif callable(hf_overrides):
                # If hf_overrides doesn't modify model_type, it will be passed straight
                # through and remain unchanged by this elif block
                dummy_model_type = f"dummy_{model_type}"
                dummy_kwargs = dict(architectures=[""], model_type=dummy_model_type)
                dummy_config = PretrainedConfig(**dummy_kwargs)
                dummy_model_type = hf_overrides(dummy_config).model_type
                model_type = dummy_model_type.removeprefix("dummy_")

        if model_type in _SPECULATIVE_DECODING_CONFIGS:
            config_class = _CONFIG_REGISTRY[model_type]
            config = config_class.from_pretrained(
                model,
                revision=revision,
                code_revision=code_revision,
                trust_remote_code=trust_remote_code,
                **kwargs,
            )
        else:
            if model_type in _CONFIG_REGISTRY:
                # Register the config class to AutoConfig to ensure it's used in future
                # calls to `from_pretrained`
                config_class = _CONFIG_REGISTRY[model_type]
                config_class.model_type = model_type
                AutoConfig.register(model_type, config_class, exist_ok=True)
                # If the on-disk model_type differs from the overridden
                # one, register under both so AutoConfig.from_pretrained
                # returns the correct class regardless of what the
                # checkpoint says
                if (
                    config_model_type := config_dict.get("model_type")
                ) and config_model_type != model_type:
                    config_class.model_type = config_model_type
                    AutoConfig.register(config_model_type, config_class, exist_ok=True)
                    config_class.model_type = model_type
                # Now that it is registered, it is not considered remote code anymore
                trust_remote_code = False
            try:
                kwargs = _maybe_update_auto_config_kwargs(kwargs, model_type=model_type)
                config = AutoConfig.from_pretrained(
                    model,
                    trust_remote_code=trust_remote_code,
                    revision=revision,
                    code_revision=code_revision,
                    **kwargs,
                )
            except ValueError as e:
                if (
                    not trust_remote_code
                    and "requires you to execute the configuration file" in str(e)
                ):
                    err_msg = (
                        "Failed to load the model config. If the model "
                        "is a custom model not yet available in the "
                        "HuggingFace transformers library, consider setting "
                        "`trust_remote_code=True` in LLM or using the "
                        "`--trust-remote-code` flag in the CLI."
                    )
                    raise RuntimeError(err_msg) from e
                else:
                    raise e
        config = _maybe_remap_hf_config_attrs(config)
        return config_dict, config