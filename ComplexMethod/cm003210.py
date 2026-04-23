def write_model(
    model_path,
    input_base_path,
    include_tokenizer=True,
    tokenizer_id=None,
    tmp_cleanup=True,
):
    os.makedirs(model_path, exist_ok=True)
    tmp_model_path = os.path.join(model_path, "tmp")
    os.makedirs(tmp_model_path, exist_ok=True)

    config_path = Path(input_base_path) / "config.json"
    olmo3_config = json.loads(config_path.read_text())
    model_config = olmo3_config["model"]
    block_config = model_config["block"]
    attention_config = block_config["attention"]
    tokenizer_config = olmo3_config["dataset"]["tokenizer"]

    n_layers = model_config["n_layers"]
    n_heads = attention_config["n_heads"]
    dim = model_config["d_model"]
    dims_per_head = dim // n_heads
    base = attention_config["rope"]["theta"]
    inv_freq = 1.0 / (base ** (torch.arange(0, dims_per_head, 2).float() / dims_per_head))
    max_position_embeddings = olmo3_config["train_module"]["max_sequence_length"]

    if attention_config.get("n_kv_heads", None) is not None:
        num_key_value_heads = model_config["n_kv_heads"]  # for GQA / MQA
    else:
        num_key_value_heads = n_heads

    print(f"Fetching all parameters from the checkpoint at {input_base_path}.")

    # Not sharded
    # (The sharded implementation would also work, but this is simpler.)
    loaded = load_model(os.path.join(input_base_path, "model_and_optim"))["model"]
    print(loaded.keys())
    # loaded = torch.load(os.path.join(input_base_path, "model.pt"), map_location="cpu", weights_only=True)

    param_count = 0
    index_dict: dict[str, Any] = {"weight_map": {}}
    for layer_i in range(n_layers):
        filename = f"pytorch_model-{layer_i + 1}-of-{n_layers + 1}.bin"
        # Unsharded
        state_dict = {
            f"model.layers.{layer_i}.self_attn.q_proj.weight": loaded[f"blocks.{layer_i}.attention.w_q.weight"],
            f"model.layers.{layer_i}.self_attn.k_proj.weight": loaded[f"blocks.{layer_i}.attention.w_k.weight"],
            f"model.layers.{layer_i}.self_attn.v_proj.weight": loaded[f"blocks.{layer_i}.attention.w_v.weight"],
            f"model.layers.{layer_i}.self_attn.o_proj.weight": loaded[f"blocks.{layer_i}.attention.w_out.weight"],
            f"model.layers.{layer_i}.self_attn.q_norm.weight": loaded[f"blocks.{layer_i}.attention.q_norm.weight"],
            f"model.layers.{layer_i}.self_attn.k_norm.weight": loaded[f"blocks.{layer_i}.attention.k_norm.weight"],
            f"model.layers.{layer_i}.mlp.gate_proj.weight": loaded[f"blocks.{layer_i}.feed_forward.w1.weight"],
            f"model.layers.{layer_i}.mlp.down_proj.weight": loaded[f"blocks.{layer_i}.feed_forward.w2.weight"],
            f"model.layers.{layer_i}.mlp.up_proj.weight": loaded[f"blocks.{layer_i}.feed_forward.w3.weight"],
            f"model.layers.{layer_i}.post_attention_layernorm.weight": loaded[
                f"blocks.{layer_i}.attention_norm.weight"
            ],
            f"model.layers.{layer_i}.post_feedforward_layernorm.weight": loaded[
                f"blocks.{layer_i}.feed_forward_norm.weight"
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
        "model.embed_tokens.weight": loaded["embeddings.weight"],
        "model.norm.weight": loaded["lm_head.norm.weight"],
        "lm_head.weight": loaded["lm_head.w_out.weight"],
    }

    for k, v in state_dict.items():
        index_dict["weight_map"][k] = filename
        param_count += v.numel()
    torch.save(state_dict, os.path.join(tmp_model_path, filename))

    # Write configs
    index_dict["metadata"] = {"total_size": param_count * 2}
    write_json(index_dict, os.path.join(tmp_model_path, "pytorch_model.bin.index.json"))

    config = Olmo3Config(
        vocab_size=model_config["vocab_size"],
        hidden_size=dim,
        intermediate_size=block_config["feed_forward"]["hidden_size"],
        num_hidden_layers=n_layers,
        num_attention_heads=n_heads,
        num_key_value_heads=num_key_value_heads,
        max_position_embeddings=max_position_embeddings,
        pad_token_id=tokenizer_config["pad_token_id"],
        bos_token_id=None,
        eos_token_id=tokenizer_config["eos_token_id"],
        tie_word_embeddings=False,
        rms_norm_eps=block_config["layer_norm"]["eps"],
        rope_theta=base,
    )
    config.save_pretrained(tmp_model_path)

    # Make space so we can load the model properly now.
    del state_dict
    del loaded
    gc.collect()

    if include_tokenizer:
        tokenizer_id = tokenizer_id or tokenizer_config["identifier"]
        _write_tokenizer(model_path, tokenizer_id)

    print("Loading the checkpoint in a Olmo 3 model.")
    model = Olmo3ForCausalLM.from_pretrained(tmp_model_path, dtype=torch.bfloat16)
    print("Resizing token embeddings to match tokenizer config.")
    model.resize_token_embeddings(tokenizer_config["vocab_size"])
    # Avoid saving this as part of the config.
    del model.config._name_or_path
    print("Saving in the Transformers format.")
    model.save_pretrained(model_path)
    if tmp_cleanup:
        # Make cleanup optional; attempting to `rmtree` the `tmp_model_path` causes
        # errors if using NFS.
        shutil.rmtree(tmp_model_path)