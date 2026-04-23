def write_model(
    model_path,
    input_base_path,
    mxfp4=False,
):
    os.makedirs(model_path, exist_ok=True)
    eos_token_id = 200002
    pad_token_id = 199999

    original_config = json.loads((Path(input_base_path) / "config.json").read_text())

    # GPT OSS Models are distributed with either num_experts or num_local_experts depending whether the original subfolder
    # or the root folder is used.
    num_local_experts = original_config.get("num_experts") or original_config.get("num_local_experts")
    if num_local_experts is None:
        raise ValueError("num_local_experts or num_experts must be specified in the config.")

    # Handle both old and new config formats for rope_parameters
    if "rope_parameters" in original_config:
        # New format: rope_parameters already exists as a dict
        rope_parameters = original_config.pop("rope_parameters")
        # Ensure rope_type is set
        if "rope_type" not in rope_parameters:
            rope_parameters["rope_type"] = "yarn"
    else:
        # Old format: construct rope_parameters from individual keys with defaults matching GptOssConfig
        rope_parameters = {
            "factor": float(original_config.pop("rope_parameters_factor", 32.0)),
            "beta_fast": float(original_config.pop("rope_ntk_beta", 32.0)),
            "beta_slow": float(original_config.pop("rope_ntk_alpha", 1.0)),
            "rope_type": "yarn",
            "truncate": False,
            "original_max_position_embeddings": 4096,
        }

    config = GptOssConfig(
        num_local_experts=num_local_experts,
        rope_parameters=rope_parameters,
        eos_token_id=eos_token_id,
        pad_token_id=pad_token_id,
        **original_config,
    )

    print(f"Fetching all parameters from the checkpoint at {input_base_path}...")
    final_ = {}
    for file in list(os.listdir(input_base_path)):
        if file.endswith(".safetensors"):
            final_.update(safe_load(os.path.join(input_base_path, file)))

    print("Converting ..")
    all_keys = final_.keys()
    new_keys = convert_old_keys_to_new_keys(all_keys)

    state_dict = {}
    for key in all_keys:
        # Post-process the current_parameter.
        new_key = new_keys.get(key, key)
        if "lm_head" not in new_key:
            new_key = "model." + new_key
        print(f"Processing key: {key} -> {new_key}")
        if re.search("qkv_proj", new_key):
            q_len = config.head_dim * config.num_attention_heads
            k_len = config.head_dim * config.num_key_value_heads
            q, k, v = (
                final_[key][:q_len, ...],
                final_[key][q_len : k_len + q_len, ...],
                final_[key][k_len + q_len :, ...],
            )
            q_key = re.sub(r"qkv_proj", "q_proj", new_key)
            k_key = re.sub(r"qkv_proj", "k_proj", new_key)
            v_key = re.sub(r"qkv_proj", "v_proj", new_key)
            state_dict[q_key] = q.contiguous().to(torch.bfloat16)
            state_dict[k_key] = k.contiguous().to(torch.bfloat16)
            state_dict[v_key] = v.contiguous().to(torch.bfloat16)
        elif re.search("gate_up_proj|down_proj", new_key) and "bias" not in new_key:
            if not mxfp4:
                if "scales" in new_key:
                    continue
                elif "blocks" in new_key:
                    # deal with packed weights
                    blocks = final_[key]
                    scales = final_[key.replace("blocks", "scales")]
                    new_key = new_key.replace(".blocks", "")
                    unpacked_tensors = convert_moe_packed_tensors(blocks, scales, dtype=torch.bfloat16)
                    state_dict[new_key] = unpacked_tensors
                else:
                    raise (f"Unidentified {key}, please double check the state dict")
            else:
                if "scales" in new_key:
                    new_key = new_key.replace(".scales", "_scales")
                    state_dict[new_key] = final_[key].contiguous()
                elif "blocks" in new_key:
                    new_key = new_key.replace(".blocks", "_blocks")
                    state_dict[new_key] = final_[key].contiguous()
                else:
                    raise (f"Unidentified {key}, please double check the state dict")
        else:
            weight = final_[key]
            if not re.search("norm", new_key):
                weight = weight.to(torch.bfloat16)  # norms are the only ones in float32
            state_dict[new_key] = weight

    del final_
    gc.collect()

    if not mxfp4:
        print("Loading the checkpoint in a GptOss model for unpacked format")
        with torch.device("meta"):
            model = GptOssForCausalLM(config)
        model.load_state_dict(state_dict, strict=True, assign=True)
        print("Checkpoint loaded successfully.")
        del config._name_or_path

        print("Saving the model")
        model.save_pretrained(model_path)
        del state_dict, model

    else:
        print("Saving the checkpoint in mxfp4 format")
        config.quantization_config = {
            "quant_method": "mxfp4",
            "modules_to_not_convert": [
                "model.layers.*.self_attn",
                "model.layers.*.mlp.router",
                "model.embed_tokens",
                "lm_head",
            ],
        }
        # required as we don't save the model with save_pretrained
        config.architectures = ["GptOssForCausalLM"]
        config.save_pretrained(model_path)
        save_sharded_model(state_dict, model_path)
        del state_dict

    gc.collect()
    print("Reloading the model to check if it's saved correctly.")
    GptOssForCausalLM.from_pretrained(model_path, dtype=torch.bfloat16, device_map="auto")
    print("Model reloaded successfully.")

    # generation config
    print("Saving generation config...")
    generation_config = GenerationConfig(
        bos_token_id=199998,  # <|startoftext|>
        do_sample=True,
        eos_token_id=[200002, 199999],  # <|return|>, <|endoftext|>
        pad_token_id=199999,  # <|endoftext|>
        temperature=1.0,
        top_p=1.0,
    )
    generation_config.save_pretrained(model_path)