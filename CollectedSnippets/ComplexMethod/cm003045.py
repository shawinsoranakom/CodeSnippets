def merge_and_shard_weights(src_root: Path, dst_root: Path, processor: MusicFlamingoProcessor):
    state: dict[str, Any] = {}
    for tag in PREFIX_MAP.keys():
        comp = _resolve_component_dir(src_root / tag)
        if not comp:
            continue

        out_prefix = PREFIX_MAP.get(tag, tag)

        if comp[0] == "file":
            fp: Path = comp[1]
            with safe_open(str(fp), framework="pt", device="cpu") as f:
                for k in f.keys():
                    if k == "__metadata__":
                        continue
                    state[f"{out_prefix}.{k}"] = f.get_tensor(k)
        else:
            base: Path = comp[1]
            shard_map: dict[str, list[str]] = comp[2]
            for shard, keys in shard_map.items():
                sp = base / shard
                with safe_open(str(sp), framework="pt", device="cpu") as f:
                    for k in keys:
                        state[f"{out_prefix}.{k}"] = f.get_tensor(k)

    if not state:
        raise FileNotFoundError("No tensors found in llm/, sound_tower/, or sound_mm_projector/.")

    tok = processor.tokenizer

    text_config = Qwen2Config(
        bos_token_id=tok.bos_token_id,
        eos_token_id=tok.eos_token_id,
        pad_token_id=tok.pad_token_id,
        vocab_size=len(tok),
        hidden_size=3584,
        intermediate_size=18944,
        model_max_length=8192,
        num_attention_heads=28,
        num_hidden_layers=28,
        num_key_value_heads=4,
        rope_theta=1000000.0,
        use_cache=False,
    )
    vocab = tok.get_vocab()
    config = MusicFlamingoConfig(
        text_config=text_config,
        audio_token_id=vocab["<sound>"],
        audio_bos_token_id=vocab.get("<|sound_bos|>"),
        audio_eos_token_id=vocab.get("<|sound_eos|>"),
        audio_rotary_dim=256,
        rope_parameters={"rope_type": "default", "rope_theta": 1200},
    )
    model = MusicFlamingoForConditionalGeneration(config).to(dtype=torch.bfloat16)

    # Update state dict to new key names if necessary
    projector_key_mapping = {
        "multi_modal_projector.layers.0.weight": "multi_modal_projector.linear_1.weight",
        "multi_modal_projector.layers.0.bias": "multi_modal_projector.linear_1.bias",
        "multi_modal_projector.layers.2.weight": "multi_modal_projector.linear_2.weight",
        "multi_modal_projector.layers.2.bias": "multi_modal_projector.linear_2.bias",
    }
    for old_key, new_key in projector_key_mapping.items():
        if old_key in state:
            state[new_key] = state.pop(old_key)

    # Llama-style rotary caches `inv_freq` as a non-persistent buffer, so we do not load/save it in the checkpoint.
    state.pop("audio_tower.sound_tower.pos_emb.freqs", None)

    # Load weights into the instantiated model so we can push via `push_to_hub` later.
    load_res = model.load_state_dict(state, strict=True)
    # Enforce a clean load
    if getattr(load_res, "missing_keys", None) and load_res.missing_keys:
        mk = load_res.missing_keys
        raise ValueError(f"Missing keys when loading: {mk[:10]}{' ...' if len(mk) > 10 else ''}")
    if getattr(load_res, "unexpected_keys", None) and load_res.unexpected_keys:
        uk = load_res.unexpected_keys
        raise ValueError(f"Unexpected keys when loading: {uk[:10]}{' ...' if len(uk) > 10 else ''}")

    generation_config = GenerationConfig(
        bos_token_id=tok.bos_token_id,
        eos_token_id=tok.eos_token_id,
        pad_token_id=tok.pad_token_id,
        max_new_tokens=2048,
    )
    model.generation_config = generation_config

    model.save_pretrained(save_directory=str(dst_root))
    logger.info("model.safetensors index and shards")
    return model