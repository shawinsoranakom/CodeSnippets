def load_kt_pretrained_model(config: "PretrainedConfig", model_args: "ModelArguments") -> "PreTrainedModel":
    r"""Optionally load pretrained model with KTransformers. Used in training."""
    custom_models = {
        "DeepseekV2ForCausalLM": DeepseekV2ForCausalLM,
        "DeepseekV3ForCausalLM": DeepseekV3ForCausalLM,
        "Qwen2MoeForCausalLM": Qwen2MoeForCausalLM,
        "Qwen3MoeForCausalLM": Qwen3MoeForCausalLM,
        "LlamaForCausalLM": LlamaForCausalLM,
        "MixtralForCausalLM": MixtralForCausalLM,
    }
    Config().cpu_infer = model_args.cpu_infer
    Config().chunk_size = model_args.chunk_size
    config = AutoConfig.from_pretrained(model_args.model_name_or_path, trust_remote_code=model_args.trust_remote_code)

    if model_args.mode == "long_context":
        assert config.architectures[0] == "LlamaForCausalLM", "only LlamaForCausalLM support long_context mode"
        torch.set_default_dtype(torch.float16)
    else:
        torch.set_default_dtype(config.torch_dtype)

    with torch.device("meta"):
        if config.architectures[0] in custom_models:
            print("using custom modeling_xxx.py.")
            if "Qwen2Moe" in config.architectures[0]:  # Qwen2Moe must use flash_attention_2 to avoid overflow.
                config._attn_implementation = "flash_attention_2"
            if "Llama" in config.architectures[0]:
                config._attn_implementation = "eager"
            if "Mixtral" in config.architectures[0]:
                config._attn_implementation = "flash_attention_2"
            model = custom_models[config.architectures[0]](config)
        else:
            attn_implementation = "flash_attention_2"
            model = AutoModelForCausalLM.from_config(
                config, trust_remote_code=True, attn_implementation=attn_implementation
            )

    optimize_config_path = model_args.kt_optimize_rule
    gguf_path = model_args.model_name_or_path

    assert optimize_config_path is not None, "optimize_config_path must be provided (path to YAML rules file)."
    assert gguf_path is not None, "gguf_path must be provided (path to a folder or .gguf file)."

    GLOBAL_CONFIG._config["mod"] = "infer"
    optimize_and_load_gguf(model, optimize_config_path, gguf_path, config)

    return model