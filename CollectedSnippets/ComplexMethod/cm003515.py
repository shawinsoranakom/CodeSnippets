def convert_and_write_model(
    input_dir: Path,
    output_dir: Path,
    max_position_embeddings: int,
    output_format: str,
) -> Mistral3Config | Mistral4Config:
    r"""Convert weights and write the HF model to output_dir."""
    params = _read_json(input_dir / "params.json")
    is_vision = params.get("vision_encoder") is not None
    is_fp8_source = params.get("quantization", {}).get("qformat_weight") == "fp8_e4m3"
    output_fp8 = output_format == "fp8" and is_fp8_source
    output_bf16 = not output_fp8

    config = convert_config(params, max_position_embeddings, is_vision, output_fp8)

    text_config = config.text_config if isinstance(config, Mistral3Config) else config
    n_experts = text_config.n_routed_experts
    vision_config = config.vision_config if isinstance(config, Mistral3Config) else None

    model_prefix = "model.language_model" if is_vision else "model"
    text_renamings = _get_text_renamings(model_prefix)
    vision_renamings = _get_vision_renamings() if is_vision else []

    full_state_dict: dict[str, torch.Tensor] = {}
    all_expert_weights: dict[tuple, torch.Tensor] = {}
    total_keys_seen: set[str] = set()
    shards = sorted(p for p in input_dir.iterdir() if p.suffix == ".safetensors")
    assert shards, f"No .safetensors files found in {input_dir}"

    for shard_path in shards:
        print(f"Processing shard: {shard_path.name}")
        original = load_file(str(shard_path))
        new_dict, expert_weights = convert_state_dict(
            original,
            text_renamings,
            vision_renamings,
            total_keys_seen,
            vision_config,
            is_fp8_source,
            output_bf16,
        )
        del original
        full_state_dict.update(new_dict)
        del new_dict
        all_expert_weights.update(expert_weights)
        del expert_weights

    print(f"Fusing {len(all_expert_weights)} expert weight entries...")
    fused = fuse_experts(all_expert_weights, n_experts, is_vision, output_fp8)
    del all_expert_weights
    full_state_dict.update(fused)
    del fused

    if text_config.tie_word_embeddings:
        full_state_dict["lm_head.weight"] = full_state_dict[f"{model_prefix}.embed_tokens.weight"]

    with torch.device("meta"):
        if isinstance(config, Mistral3Config):
            model = Mistral3ForConditionalGeneration(config)
        else:
            model = Mistral4ForCausalLM(config)

        if output_fp8 and hasattr(model.config, "quantization_config"):
            qconfig = model.config.quantization_config
            model = replace_with_fp8_linear(model, qconfig.modules_to_not_convert, qconfig)

    model.load_state_dict(full_state_dict, strict=True, assign=True)
    model.save_pretrained(str(output_dir))
    return config