def get_quant_config(
    model_config: ModelConfig, load_config: LoadConfig
) -> QuantizationConfig:
    if model_config.quantization is None:
        raise ValueError("Model quantization method is not specified in the config.")
    quant_cls = get_quantization_config(model_config.quantization)

    # GGUF doesn't have config file
    if model_config.quantization == "gguf":
        return quant_cls()

    # Read the quantization config from the HF model config, if available.
    hf_quant_config = getattr(model_config.hf_config, "quantization_config", None)
    # some vision model may keep quantization_config in their text_config
    hf_text_config = getattr(model_config.hf_config, "text_config", None)
    if hf_quant_config is None and hf_text_config is not None:
        hf_quant_config = getattr(hf_text_config, "quantization_config", None)
    if hf_quant_config is None:
        # compressed-tensors uses a compressions_config
        hf_quant_config = getattr(model_config.hf_config, "compression_config", None)

    # Pipe information about heads to enable TP-aware loading of attn_head scales
    if (
        hf_quant_config is not None
        and hf_quant_config.get("quant_method") == "compressed-tensors"
        and "config_groups" in hf_quant_config
    ):
        if hf_text_config is not None:
            n_heads = getattr(hf_text_config, "num_attention_heads", None)
            n_kv_heads = getattr(hf_text_config, "num_key_value_heads", None)
        else:
            n_heads = getattr(model_config.hf_config, "num_attention_heads", None)
            n_kv_heads = getattr(model_config.hf_config, "num_key_value_heads", None)

        hf_quant_config["total_num_heads"] = n_heads
        hf_quant_config["total_num_kv_heads"] = (
            n_kv_heads if n_kv_heads is not None else n_heads
        )

    if hf_quant_config is not None:
        if model_config.quantization_config is not None:
            raise ValueError(
                "Setting `quantization_config` for online "
                "quantization when the model checkpoint already "
                "has a `quantization_config` is not supported"
            )

        # For modelopt_mixed, config.json's quantization_config may or may
        # not contain the per-layer quantized_layers map.  Newer checkpoints
        # embed it directly; older ones keep it only in hf_quant_config.json.
        # If it is missing, fall through to the file-based loading path.
        if (
            model_config.quantization == "modelopt_mixed"
            and "quantized_layers" not in hf_quant_config
        ):
            pass  # fall through to file-based loading below
        else:
            return quant_cls.from_config(hf_quant_config)

    # if hf_quant_config is None, we will try to get config from
    # hf_overrides
    hf_overrides = model_config.hf_overrides
    if not isinstance(hf_overrides, dict):
        raise ValueError(
            "hf_overrides must be a dict for get_quant_config "
            "to get the quantization config from it."
        )
    quantization_config_file = hf_overrides.get("quantization_config_file", None)
    if quantization_config_file is not None:
        if hasattr(quant_cls, "from_config_file"):
            if model_config.quantization_config is not None:
                raise ValueError(
                    "Setting `quantization_config` for online "
                    "quantization when the model checkpoint already "
                    "has a `quantization_config` is not supported"
                )
            return quant_cls.from_config_file(quantization_config_file)
        else:
            raise NotImplementedError(
                "from_config_file is specified in hf_override config, "
                "but quant_cls.from_config_file is not implemented in "
                f"{quant_cls}"
            )
    quantization_config_json = hf_overrides.get("quantization_config_dict_json", None)
    if quantization_config_json is not None:
        if hasattr(quant_cls, "from_config_dict_json"):
            if model_config.quantization_config is not None:
                raise ValueError(
                    "Setting `quantization_config` for online "
                    "quantization when the model checkpoint already "
                    "has a `quantization_config` is not supported"
                )
            return quant_cls.from_config_dict_json(quantization_config_json)
        else:
            raise NotImplementedError(
                "from_config_dict_json is specified in hf_override config, "
                "but quant_cls.from_config_dict_json is not implemented in "
                f"{quant_cls}"
            )

    # Online quantization doesn't read from checkpoint configs — it quantizes
    # fp16/bf16 weights on the fly during loading.
    if model_config.quantization_config is not None:
        from vllm.config.quantization import OnlineQuantizationConfigArgs
        from vllm.model_executor.layers.quantization.online.base import (
            OnlineQuantizationConfig,
        )

        assert isinstance(
            model_config.quantization_config, OnlineQuantizationConfigArgs
        )
        return OnlineQuantizationConfig(args=model_config.quantization_config)

    # Inflight BNB quantization
    if model_config.quantization == "bitsandbytes":
        return quant_cls.from_config({})
    model_name_or_path = (
        maybe_download_from_modelscope(
            model_config.model,
            revision=model_config.revision,
            download_dir=load_config.download_dir,
            allow_patterns=["*.json"],
        )
        or model_config.model
    )
    is_local = os.path.isdir(model_name_or_path)
    if not is_local:
        # Download the config files.
        with get_lock(model_config.model, load_config.download_dir):
            hf_folder = snapshot_download(
                model_config.model,
                revision=model_config.revision,
                allow_patterns="*.json",
                cache_dir=load_config.download_dir,
                local_files_only=huggingface_hub.constants.HF_HUB_OFFLINE,
                tqdm_class=DisabledTqdm,
            )
    else:
        hf_folder = model_name_or_path

    possible_config_filenames = quant_cls.get_config_filenames()

    # If the quantization config is not found, use the default config.
    if not possible_config_filenames:
        return quant_cls()

    config_files = glob.glob(os.path.join(hf_folder, "*.json"))

    quant_config_files = [
        f for f in config_files if any(f.endswith(x) for x in possible_config_filenames)
    ]
    if len(quant_config_files) == 0:
        raise ValueError(f"Cannot find the config file for {model_config.quantization}")
    if len(quant_config_files) > 1:
        raise ValueError(
            f"Found multiple config files for {model_config.quantization}: "
            f"{quant_config_files}"
        )

    quant_config_file = quant_config_files[0]
    with open(quant_config_file) as f:
        config = json.load(f)

        if model_config.quantization == "bitsandbytes":
            config["adapter_name_or_path"] = model_config.model
        elif model_config.quantization in ("modelopt", "modelopt_mixed"):
            if config.get("producer", {}).get("name") == "modelopt":
                return quant_cls.from_config(config)
            else:
                raise ValueError(
                    f"Unsupported quantization config"
                    f" found for {model_config.quantization} in {f}."
                )

    return quant_cls.from_config(config)