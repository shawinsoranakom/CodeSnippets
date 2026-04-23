def write_model(model_path, input_base_path, tokenizer_path=None, fix_eos_token_id=True):
    os.makedirs(model_path, exist_ok=True)
    tmp_model_path = os.path.join(model_path, "tmp")
    os.makedirs(tmp_model_path, exist_ok=True)

    config_path = Path(input_base_path) / "config.yaml"
    olmoe_config = yaml.safe_load(config_path.read_text())["model"]

    if fix_eos_token_id:
        olmoe_config["eos_token_id"] = 50279

    n_layers = olmoe_config["n_layers"]
    n_heads = olmoe_config["n_heads"]
    dim = olmoe_config["d_model"]
    dims_per_head = dim // n_heads
    base = 10000.0
    inv_freq = 1.0 / (base ** (torch.arange(0, dims_per_head, 2).float() / dims_per_head))
    max_position_embeddings = olmoe_config["max_sequence_length"]

    vocab_size = olmoe_config.get("embedding_size", olmoe_config["vocab_size"])

    if olmoe_config.get("n_kv_heads", None) is not None:
        num_key_value_heads = olmoe_config["n_kv_heads"]  # for GQA / MQA
    elif olmoe_config["multi_query_attention"]:  # compatibility with other checkpoints
        num_key_value_heads = 1
    else:
        num_key_value_heads = n_heads

    print(f"Fetching all parameters from the checkpoint at {input_base_path}.")

    # Not sharded
    loaded = torch.load(os.path.join(input_base_path, "model.pt"), map_location="cpu", weights_only=True)

    param_count = 0
    index_dict = {"weight_map": {}}
    for layer_i in range(n_layers):
        filename = f"pytorch_model-{layer_i + 1}-of-{n_layers + 1}.bin"
        fused_dims = [dim, dims_per_head * num_key_value_heads, dims_per_head * num_key_value_heads]
        q_proj_weight, k_proj_weight, v_proj_weight = torch.split(
            loaded[f"transformer.blocks.{layer_i}.att_proj.weight"], fused_dims, dim=0
        )
        state_dict = {
            f"model.layers.{layer_i}.self_attn.q_proj.weight": q_proj_weight,
            f"model.layers.{layer_i}.self_attn.k_proj.weight": k_proj_weight,
            f"model.layers.{layer_i}.self_attn.v_proj.weight": v_proj_weight,
            f"model.layers.{layer_i}.self_attn.o_proj.weight": loaded[f"transformer.blocks.{layer_i}.attn_out.weight"],
            f"model.layers.{layer_i}.self_attn.q_norm.weight": loaded[f"transformer.blocks.{layer_i}.q_norm.weight"],
            f"model.layers.{layer_i}.self_attn.k_norm.weight": loaded[f"transformer.blocks.{layer_i}.k_norm.weight"],
            f"model.layers.{layer_i}.mlp.gate.weight": loaded[f"transformer.blocks.{layer_i}.ffn.router.layer.weight"],
            f"model.layers.{layer_i}.input_layernorm.weight": loaded[f"transformer.blocks.{layer_i}.attn_norm.weight"],
            f"model.layers.{layer_i}.post_attention_layernorm.weight": loaded[
                f"transformer.blocks.{layer_i}.ff_norm.weight"
            ],
        }

        num_experts = loaded[f"transformer.blocks.{layer_i}.ffn.router.layer.weight"].shape[0]
        dim_per_expert = loaded[f"transformer.blocks.{layer_i}.ffn.experts.mlp.w1"].shape[0] // num_experts
        for expert_i in range(num_experts):
            state_dict[f"model.layers.{layer_i}.mlp.experts.{expert_i}.gate_proj.weight"] = loaded[
                f"transformer.blocks.{layer_i}.ffn.experts.mlp.w1"
            ][dim_per_expert * expert_i : dim_per_expert * (expert_i + 1), :]
            state_dict[f"model.layers.{layer_i}.mlp.experts.{expert_i}.up_proj.weight"] = loaded[
                f"transformer.blocks.{layer_i}.ffn.experts.mlp.v1"
            ][dim_per_expert * expert_i : dim_per_expert * (expert_i + 1), :]
            state_dict[f"model.layers.{layer_i}.mlp.experts.{expert_i}.down_proj.weight"] = loaded[
                f"transformer.blocks.{layer_i}.ffn.experts.mlp.w2"
            ][dim_per_expert * expert_i : dim_per_expert * (expert_i + 1), :].T.contiguous()

        state_dict[f"model.layers.{layer_i}.self_attn.rotary_emb.inv_freq"] = inv_freq

        for k, v in state_dict.items():
            index_dict["weight_map"][k] = filename
            param_count += v.numel()
        torch.save(state_dict, os.path.join(tmp_model_path, filename))

    filename = f"pytorch_model-{n_layers + 1}-of-{n_layers + 1}.bin"

    # Unsharded
    state_dict = {
        "model.embed_tokens.weight": loaded["transformer.wte.weight"],
        "lm_head.weight": loaded["transformer.ff_out.weight"],
        "model.norm.weight": loaded["transformer.ln_f.weight"],
    }

    for k, v in state_dict.items():
        index_dict["weight_map"][k] = filename
        param_count += v.numel()
    torch.save(state_dict, os.path.join(tmp_model_path, filename))

    # Write configs
    index_dict["metadata"] = {"total_size": param_count * 2}
    write_json(index_dict, os.path.join(tmp_model_path, "pytorch_model.bin.index.json"))

    config = OlmoeConfig(
        vocab_size=vocab_size,
        hidden_size=dim,
        intermediate_size=dim_per_expert,
        num_hidden_layers=n_layers,
        num_attention_heads=n_heads,
        num_key_value_heads=num_key_value_heads,
        max_position_embeddings=max_position_embeddings,
        pad_token_id=olmoe_config["pad_token_id"],
        bos_token_id=None,
        eos_token_id=olmoe_config["eos_token_id"],
        tie_word_embeddings=olmoe_config["weight_tying"],
        rope_theta=base,
        clip_qkv=olmoe_config.get("clip_qkv"),
    )
    config.save_pretrained(tmp_model_path)

    # Make space so we can load the model properly now.
    del state_dict
    del loaded
    gc.collect()

    if tokenizer_path is not None:
        _write_tokenizer(model_path, config, tokenizer_path, fix_eos_token_id)

    print("Loading the checkpoint in a OLMoE model.")
    model = OlmoeForCausalLM.from_pretrained(tmp_model_path, dtype=torch.bfloat16)
    # Avoid saving this as part of the config.
    del model.config._name_or_path
    print("Saving in the Transformers format.")
    model.save_pretrained(model_path)
    shutil.rmtree(tmp_model_path)