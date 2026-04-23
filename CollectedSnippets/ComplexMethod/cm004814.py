def write_model(
    model_path,
    input_base_path,
    include_tokenizer=True,
    tokenizer_path=None,
    fix_eos_token_id=True,
    tmp_cleanup=True,
):
    os.makedirs(model_path, exist_ok=True)
    tmp_model_path = os.path.join(model_path, "tmp")
    os.makedirs(tmp_model_path, exist_ok=True)

    config_path = Path(input_base_path) / "config.yaml"
    olmo2_config = yaml.safe_load(config_path.read_text())["model"]

    if not olmo2_config.get("attention_layer_norm", False):
        raise RuntimeError("OLMo2 checkpoints must have attention layer norm")
    if not olmo2_config.get("norm_after", False):
        raise RuntimeError("OLMo2 checkpoints must set norm_after to True")

    n_layers = olmo2_config["n_layers"]
    n_heads = olmo2_config["n_heads"]
    dim = olmo2_config["d_model"]
    dims_per_head = dim // n_heads
    base = olmo2_config["rope_theta"]
    inv_freq = 1.0 / (base ** (torch.arange(0, dims_per_head, 2).float() / dims_per_head))
    max_position_embeddings = olmo2_config["max_sequence_length"]

    vocab_size = olmo2_config.get("embedding_size", olmo2_config["vocab_size"])

    if olmo2_config.get("n_kv_heads", None) is not None:
        num_key_value_heads = olmo2_config["n_kv_heads"]  # for GQA / MQA
    elif olmo2_config["multi_query_attention"]:  # compatibility with other checkpoints
        num_key_value_heads = 1
    else:
        num_key_value_heads = n_heads

    print(f"Fetching all parameters from the checkpoint at {input_base_path}.")

    # Not sharded
    # (The sharded implementation would also work, but this is simpler.)
    loaded = torch.load(os.path.join(input_base_path, "model.pt"), map_location="cpu", weights_only=True)

    param_count = 0
    index_dict: dict[str, Any] = {"weight_map": {}}
    for layer_i in range(n_layers):
        filename = f"pytorch_model-{layer_i + 1}-of-{n_layers + 1}.bin"
        # Unsharded
        # TODO: Layernorm stuff
        # TODO: multi query attention
        fused_dims = [dim, dims_per_head * num_key_value_heads, dims_per_head * num_key_value_heads]
        q_proj_weight, k_proj_weight, v_proj_weight = torch.split(
            loaded[f"transformer.blocks.{layer_i}.att_proj.weight"], fused_dims, dim=0
        )
        up_proj_weight, gate_proj_weight = torch.chunk(
            loaded[f"transformer.blocks.{layer_i}.ff_proj.weight"], 2, dim=0
        )
        state_dict = {
            f"model.layers.{layer_i}.self_attn.q_proj.weight": q_proj_weight,
            f"model.layers.{layer_i}.self_attn.k_proj.weight": k_proj_weight,
            f"model.layers.{layer_i}.self_attn.v_proj.weight": v_proj_weight,
            f"model.layers.{layer_i}.self_attn.o_proj.weight": loaded[f"transformer.blocks.{layer_i}.attn_out.weight"],
            f"model.layers.{layer_i}.self_attn.q_norm.weight": loaded[f"transformer.blocks.{layer_i}.q_norm.weight"],
            f"model.layers.{layer_i}.self_attn.k_norm.weight": loaded[f"transformer.blocks.{layer_i}.k_norm.weight"],
            f"model.layers.{layer_i}.mlp.gate_proj.weight": gate_proj_weight,
            f"model.layers.{layer_i}.mlp.down_proj.weight": loaded[f"transformer.blocks.{layer_i}.ff_out.weight"],
            f"model.layers.{layer_i}.mlp.up_proj.weight": up_proj_weight,
            f"model.layers.{layer_i}.post_attention_layernorm.weight": loaded[
                f"transformer.blocks.{layer_i}.attn_norm.weight"
            ],
            f"model.layers.{layer_i}.post_feedforward_layernorm.weight": loaded[
                f"transformer.blocks.{layer_i}.ff_norm.weight"
            ],
        }

        state_dict[f"model.layers.{layer_i}.self_attn.rotary_emb.inv_freq"] = inv_freq

        for k, v in state_dict.items():
            index_dict["weight_map"][k] = filename
            param_count += v.numel()
        torch.save(state_dict, os.path.join(tmp_model_path, filename))

    filename = f"pytorch_model-{n_layers + 1}-of-{n_layers + 1}.bin"

    # Unsharded
    # TODO: Deal with weight-tying
    state_dict = {
        "model.embed_tokens.weight": loaded["transformer.wte.weight"],
        "model.norm.weight": loaded["transformer.ln_f.weight"],
        "lm_head.weight": loaded["transformer.ff_out.weight"]
        if "transformer.ff_out.weight" in loaded
        else loaded["transformer.wte.weight"],
    }

    for k, v in state_dict.items():
        index_dict["weight_map"][k] = filename
        param_count += v.numel()
    torch.save(state_dict, os.path.join(tmp_model_path, filename))

    # Write configs
    index_dict["metadata"] = {"total_size": param_count * 2}
    write_json(index_dict, os.path.join(tmp_model_path, "pytorch_model.bin.index.json"))

    if olmo2_config.get("mlp_hidden_size", None) is not None:
        intermediate_size = olmo2_config["mlp_hidden_size"] // 2
    else:
        intermediate_size = (dim * olmo2_config["mlp_ratio"]) // 2

    if fix_eos_token_id and olmo2_config["eos_token_id"] == 0:
        # Fixing a bug in OLMo where eos token id was incorrectly set
        print("Changing eos_token_id from 0 to 50279.")
        olmo2_config["eos_token_id"] = 50279

    config = Olmo2Config(
        vocab_size=vocab_size,
        hidden_size=dim,
        intermediate_size=intermediate_size,
        num_hidden_layers=n_layers,
        num_attention_heads=n_heads,
        num_key_value_heads=num_key_value_heads,
        max_position_embeddings=max_position_embeddings,
        pad_token_id=olmo2_config["pad_token_id"],
        bos_token_id=None,
        eos_token_id=olmo2_config["eos_token_id"],
        tie_word_embeddings=olmo2_config["weight_tying"],
        rms_norm_eps=olmo2_config["layer_norm_eps"],
        rope_theta=base,
    )
    config.save_pretrained(tmp_model_path)

    # Make space so we can load the model properly now.
    del state_dict
    del loaded
    gc.collect()

    if include_tokenizer:
        _write_tokenizer(model_path, config, input_base_path, tokenizer_path)

    print("Loading the checkpoint in a OLMo2 model.")
    model = Olmo2ForCausalLM.from_pretrained(tmp_model_path, dtype=torch.float32)
    # Avoid saving this as part of the config.
    del model.config._name_or_path
    print("Saving in the Transformers format.")
    model.save_pretrained(model_path)
    if tmp_cleanup:
        # Make cleanup optional; attempting to `rmtree` the `tmp_model_path` causes
        # errors if using NFS.
        shutil.rmtree(tmp_model_path)