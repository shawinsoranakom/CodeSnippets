def get_config(
    model: str | Path,
    trust_remote_code: bool,
    revision: str | None = None,
    code_revision: str | None = None,
    config_format: str | ConfigFormat = "auto",
    hf_overrides_kw: dict[str, Any] | None = None,
    hf_overrides_fn: Callable[[PretrainedConfig], PretrainedConfig] | None = None,
    **kwargs,
) -> PretrainedConfig:
    # Separate model folder from file path for GGUF models

    _is_gguf = is_gguf(model)
    _is_remote_gguf = is_remote_gguf(model)
    if _is_gguf:
        if check_gguf_file(model):
            # Local GGUF file
            kwargs["gguf_file"] = Path(model).name
            model = Path(model).parent
        elif _is_remote_gguf:
            # Remote GGUF - extract repo_id from repo_id:quant_type format
            # The actual GGUF file will be downloaded later by GGUFModelLoader
            # Keep model as repo_id:quant_type for download, but use repo_id for config
            model, _ = split_remote_gguf(model)

    if config_format == "auto":
        try:
            # First check for Mistral to avoid defaulting to
            # Transformers implementation.
            if is_mistral_model_repo(
                model_name_or_path=str(model), revision=revision
            ) and file_or_path_exists(
                model=model, config_name=MISTRAL_CONFIG_NAME, revision=revision
            ):
                config_format = "mistral"
            elif (_is_gguf and not _is_remote_gguf) or file_or_path_exists(
                model, HF_CONFIG_NAME, revision=revision
            ):
                config_format = "hf"
            # Remote GGUF models must have config.json in repo,
            # otherwise the config can't be parsed correctly.
            # FIXME(Isotr0py): Support remote GGUF repos without config.json
            elif _is_remote_gguf and not file_or_path_exists(
                model, HF_CONFIG_NAME, revision=revision
            ):
                err_msg = (
                    "Could not find config.json for remote GGUF model repo. "
                    "To load remote GGUF model through `<repo_id>:<quant_type>`, "
                    "ensure your model has config.json (HF format) file. "
                    "Otherwise please specify --hf-config-path <original_repo> "
                    "in engine args to fetch config from unquantized hf model."
                )
                logger.error(err_msg)
                raise ValueError(err_msg)
            else:
                raise ValueError(
                    "Could not detect config format for no config file found. "
                    "With config_format 'auto', ensure your model has either "
                    "config.json (HF format) or params.json (Mistral format). "
                    "Otherwise please specify your_custom_config_format "
                    "in engine args for customized config parser."
                )

        except Exception as e:
            error_message = (
                "Invalid repository ID or local directory specified:"
                " '{model}'.\nPlease verify the following requirements:\n"
                "1. Provide a valid Hugging Face repository ID.\n"
                "2. Specify a local directory that contains a recognized "
                "configuration file.\n"
                "   - For Hugging Face models: ensure the presence of a "
                "'config.json'.\n"
                "   - For Mistral models: ensure the presence of a "
                "'params.json'.\n"
            ).format(model=model)

            raise ValueError(error_message) from e

    config_parser = get_config_parser(config_format)
    config_dict, config = config_parser.parse(
        model,
        trust_remote_code=trust_remote_code,
        revision=revision,
        code_revision=code_revision,
        hf_overrides=hf_overrides_kw or hf_overrides_fn,
        **kwargs,
    )

    # Patching defaults for GGUF models
    if _is_gguf:
        # Some models have different default values between GGUF and HF.
        def apply_gguf_default(key: str, gguf_default: Any):
            """
            Apply GGUF defaults unless explicitly configured.

            This function reads/writes external `config` and `config_dict`.
            If the specified `key` is not in `config_dict` (i.e. not explicitly
            configured and the default HF value is used), it updates the
            corresponding `config` value to `gguf_default`.
            """
            if key not in config_dict:
                config.update({key: gguf_default})

        # Apply architecture-specific GGUF defaults.
        if config.model_type in {"qwen3_moe"}:
            # Qwen3 MoE: norm_topk_prob is always true.
            # Note that, this parameter is always false (HF default) on Qwen2 MoE.
            apply_gguf_default("norm_topk_prob", True)

    # Special architecture mapping check for GGUF models
    if _is_gguf:
        if config.model_type not in MODEL_FOR_CAUSAL_LM_MAPPING_NAMES:
            raise RuntimeError(f"Can't get gguf config for {config.model_type}.")
        model_type = MODEL_FOR_CAUSAL_LM_MAPPING_NAMES[config.model_type]
        config.update({"architectures": [model_type]})

    # Architecture mapping for models without explicit architectures field
    if not config.architectures:
        if config.model_type not in MODEL_MAPPING_NAMES:
            logger.warning(
                "Model config does not have a top-level 'architectures' field: "
                "expecting `hf_overrides={'architectures': ['...']}` to be passed "
                "in engine args."
            )
        else:
            model_type = MODEL_MAPPING_NAMES[config.model_type]
            config.update({"architectures": [model_type]})

    # ModelOpt 0.31.0 and after saves the quantization config in the model
    # config file.
    quantization_config = config_dict.get("quantization_config", None)

    # ModelOpt 0.29.0 and before saves the quantization config in a separate
    # "hf_quant_config.json" in the same directory as the model config file.
    if quantization_config is None and file_or_path_exists(
        model, "hf_quant_config.json", revision
    ):
        quantization_config = get_hf_file_to_dict(
            "hf_quant_config.json", model, revision
        )

    if quantization_config is not None:
        config.quantization_config = quantization_config
        # auto-enable DeepGEMM UE8M0 if model config requests it
        scale_fmt = quantization_config.get("scale_fmt", None)
        if scale_fmt in ("ue8m0",):
            if not envs.is_set("VLLM_USE_DEEP_GEMM_E8M0"):
                os.environ["VLLM_USE_DEEP_GEMM_E8M0"] = "1"
                logger.info_once(
                    (
                        "Detected quantization_config.scale_fmt=%s; "
                        "enabling UE8M0 for DeepGEMM."
                    ),
                    scale_fmt,
                )
            elif not envs.VLLM_USE_DEEP_GEMM_E8M0:
                logger.warning_once(
                    (
                        "Model config requests UE8M0 "
                        "(quantization_config.scale_fmt=%s), but "
                        "VLLM_USE_DEEP_GEMM_E8M0=0 is set; "
                        "UE8M0 for DeepGEMM disabled."
                    ),
                    scale_fmt,
                )

    if hf_overrides_kw:
        logger.debug("Overriding HF config with %s", hf_overrides_kw)
        config.update(hf_overrides_kw)
    if hf_overrides_fn:
        logger.debug("Overriding HF config with %s", hf_overrides_fn)
        config = hf_overrides_fn(config)

    # Exhaustively patch RoPE parameters everywhere they might be
    patch_rope_parameters(config)
    patch_rope_parameters(config.get_text_config())
    SubConfigs: TypeAlias = dict[str, PretrainedConfig]
    sub_configs: SubConfigs | None = getattr(config, "sub_configs", None)
    if sub_configs:
        for sub_config in sub_configs:
            patch_rope_parameters(getattr(config, sub_config))

    if trust_remote_code:
        maybe_register_config_serialize_by_value()

    return config