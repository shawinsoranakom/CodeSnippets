def write_model(
    model_path,
    input_base_path,
    num_shards,
    convert_checkpoints,
    instruct=False,
):
    os.makedirs(model_path, exist_ok=True)

    with open(os.path.join(input_base_path, "params.json"), "r") as f:
        params = json.load(f)

    params = params.get("model", params)
    dtype = "bfloat16"

    # ------------------------------------------------------------
    # Text model params and config
    # ------------------------------------------------------------

    # params from config
    vocab_size = 202048  # params["vocab_size"] # seems like the lm head is 25256 so padded instead of 202048
    num_layers = params["n_layers"]
    dim = params["dim"]
    num_heads = params["n_heads"]
    rms_norm_eps = params["norm_eps"]
    rope_theta = params["rope_theta"]
    no_rope_layer_interval = params["nope_layer_interval"]
    attention_chunk_size = params["attention_chunk_size"]

    config_kwargs = {}
    if params["use_scaled_rope"]:
        # some constants from original code
        rope_parameters = {
            "rope_type": "llama3",
            "factor": params.get("rope_parameters_factor", 8.0),
            "low_freq_factor": 1.0,
            "high_freq_factor": params.get("rope_high_freq_factor", 4.0),
            "original_max_position_embeddings": 8192,
        }
        config_kwargs.update({"rope_parameters": rope_parameters})

    if attention_chunk_size is None:
        config_kwargs.update({"cache_implementation": "static"})

    # compute additional params for weight conversion
    num_heads_per_shard = num_heads // num_shards
    dim_per_head = dim // num_heads
    intermediate_size_mlp = compute_intermediate_size(
        dim,
        ffn_exp=params["ffn_exp"],
        multiple_of=params["multiple_of"],
        ffn_dim_multiplier=params["ffn_dim_multiplier"],
    )

    num_key_value_heads = params["n_kv_heads"]  # for GQA / MQA

    if params.get("moe_args", False):
        num_experts = params["moe_args"]["num_experts"]
        interleave_moe_layer_step = params["moe_args"].get("interleave_moe_layer_step", 1)
    else:
        # Dense model (possibly Llama Guard) - disable all moe layers
        num_experts = 0
        interleave_moe_layer_step = 0
        config_kwargs.update({"moe_layers": []})

    # Ensure all layers are rope if `nope_layer_interval` is None
    no_rope_layer_interval = params["nope_layer_interval"]
    no_rope_layer_interval = num_heads * 2 if no_rope_layer_interval is None else no_rope_layer_interval

    bos_token_id = 200000
    eos_token_id = [200001, 200007, 200008] if instruct else 200001
    pad_token_id = 200018

    text_config = Llama4TextConfig(
        num_attention_heads=num_heads,
        vocab_size=vocab_size,
        hidden_size=dim,
        rms_norm_eps=rms_norm_eps,
        rope_theta=rope_theta,
        num_hidden_layers=num_layers,
        intermediate_size=8192,
        intermediate_size_mlp=intermediate_size_mlp,
        max_position_embeddings=max_context_length(input_base_path, instruct),
        num_local_experts=num_experts,
        interleave_moe_layer_step=interleave_moe_layer_step,
        use_qk_norm=params["use_qk_norm"],
        no_rope_layer_interval=no_rope_layer_interval,
        attention_chunk_size=attention_chunk_size,
        bos_token_id=bos_token_id,
        eos_token_id=eos_token_id,
        pad_token_id=pad_token_id,
        tie_word_embeddings=False,  # Constant set to False
        dtype=dtype,
        for_llm_compressor=_OFFLINE_QUANT_COMPATIBLE,
        **config_kwargs,
    )
    # default vision config from params

    vision_params = params["vision_args"]
    vision_dim = vision_params["dim"]
    vision_num_layers = vision_params["n_layers"]
    image_size = vision_params["image_size"]["height"]  # siglip config is outdated
    vision_num_heads = vision_params["n_heads"]

    vision_output_dim = vision_params["output_dim"]

    vision_config = Llama4VisionConfig(
        hidden_act="gelu",
        num_hidden_layers=vision_num_layers,
        image_size=image_size,
        num_attention_heads=vision_num_heads,
        hidden_size=vision_dim,
        vision_output_dim=vision_output_dim,
    )

    config = Llama4Config(text_config=text_config, vision_config=vision_config)
    config.save_pretrained(model_path)

    print("Model config saved successfully...")

    # ------------------------------------------------------------
    # Convert weights
    # ------------------------------------------------------------

    if convert_checkpoints:
        print(f"Fetching all parameters from the checkpoint at {input_base_path}...")
        if num_shards == 1:
            if os.path.exists(os.path.join(input_base_path, "consolidated.00.pth")):
                path = os.path.join(input_base_path, "consolidated.00.pth")
            else:
                path = os.path.join(input_base_path, "consolidated.pth")
            loaded = [safe_load(path)]
        else:
            loaded = [
                safe_load(os.path.join(input_base_path, f"consolidated.{i:02d}.pth"))
                for i in tqdm(range(num_shards), desc="Loading shards", unit="shard")
            ]
        loaded = [preprocess_keys(d) for d in loaded]

        all_keys_raw = list(loaded[0].keys())
        repeated_keys = []
        sharded_keys = []
        for _key in all_keys_raw:
            try:
                if num_shards == 1 or (loaded[0][_key] == loaded[1][_key]).all():
                    repeated_keys.append(_key)
                else:
                    sharded_keys.append(_key)
            except Exception as e:
                print(f"Encountered exception {e} for {_key}")
        print("Initializing an empty model")
        with torch.device("meta"):
            model = Llama4ForConditionalGeneration(config)

        print("Converting model...")
        all_keys = list(loaded[0].keys())
        new_keys = convert_old_keys_to_new_keys(all_keys)
        state_dict = {}
        replicated_params = []  # To keep track of replicated weights.
        for key in tqdm(all_keys, desc="Renaming and processing all keys", unit="key"):
            new_key = new_keys[key]
            print(key, new_key)
            if num_shards > 1 and not is_param_same_across_shards(new_key):
                current_parameter = [chunk.pop(key) for chunk in loaded if not isinstance(chunk[key], io.BytesIO)]
            else:
                print(f"{key} (now {new_key}) is the same across all shards.")
                replicated_params.append((key, new_key))
                current_parameter = [loaded[0].pop(key)] if not isinstance(loaded[0][key], io.BytesIO) else []

            if "running_gate_stats_3E" in key:
                new_keys.pop(new_key)
                continue

            concat_dim = get_concat_dim(new_key)

            # Post-process the current_parameter.
            if "qkv_proj" in new_key:
                queries = []
                keys = []
                values = []
                for param in current_parameter:
                    query, key_, value = param.split(
                        [
                            num_heads * dim_per_head // num_shards,
                            num_key_value_heads * dim_per_head // num_shards,
                            num_key_value_heads * dim_per_head // num_shards,
                        ]
                    )
                    queries.append(query.reshape(num_heads_per_shard, -1, dim))
                    keys.append(key_.reshape(num_key_value_heads // num_shards, -1, dim))
                    values.append(value.reshape(num_key_value_heads // num_shards, -1, dim))

                queries = torch.cat(queries, dim=0).reshape(dim, dim)
                keys = torch.cat(keys, dim=0).reshape(num_key_value_heads * dim_per_head, dim)
                values = torch.cat(values, dim=0).reshape(num_key_value_heads * dim_per_head, dim)
                # queries = permute_for_rope(queries, num_heads, dim, dim)
                # keys = permute_for_rope(keys, num_key_value_heads, num_key_value_heads*dim_per_head, dim)

                q = new_key.replace("qkv", "q")
                tqdm.write(f"Processing: {key.ljust(50)}  ->\t {q}, {queries.shape}")
                state_dict[q] = queries

                k = new_key.replace("qkv", "k")
                tqdm.write(f"Processing: {key.ljust(50)}  ->\t {k}, {keys.shape}")
                state_dict[k] = keys

                v = new_key.replace("qkv", "v")
                tqdm.write(f"Processing: {key.ljust(50)}  ->\t {v}, {values.shape}")
                state_dict[v] = values
            elif _OFFLINE_QUANT_COMPATIBLE and "feed_forward.experts." in new_key:
                # for experts, we need to split expert for offline quantization purpose and don't need to fuse
                expert_lists = []
                for k in current_parameter:
                    expert_lists.append(
                        list(k.reshape(num_experts, -1, k.shape[-1]).unbind(0))
                    )  # [#expert * IN, OUT] -> #experts * [IN, OUT]
                for i in range(num_experts):
                    expert = torch.cat([expert_list[i] for expert_list in expert_lists], dim=concat_dim)
                    expert_key = new_key.replace("experts.", f"experts.{i}.")
                    state_dict[expert_key] = expert.transpose(0, 1).contiguous()  # [OUT, IN]
                    tqdm.write(f"Processing: {key.ljust(50)}  ->\t {expert_key}, {state_dict[expert_key].shape}")
            elif re.search(r"(gate|up)_proj", new_key):
                path = new_key.split(".")
                gate_key = re.sub(r"(gate|up)_proj", lambda m: "gate_proj", new_key)
                up_key = re.sub(r"(gate|up)_proj", lambda m: "up_proj", new_key)
                if gate_key == new_key:
                    state_dict[new_key] = torch.cat(current_parameter, dim=concat_dim)
                elif new_key == up_key:
                    if "experts" not in new_key:
                        state_dict[new_key] = torch.cat(current_parameter, dim=concat_dim)
                    else:
                        gate_proj = state_dict.pop(gate_key)
                        gate_proj = [
                            gate_proj.reshape(num_experts, -1, 8, 1024)[:, :, k, :].reshape(num_experts, -1, 1024)
                            for k in range(8)
                        ]
                        gate_proj = torch.cat(gate_proj, dim=-1)

                        up_proj = [
                            k.reshape(num_experts, -1, 8, 1024).reshape(num_experts, -1, 1024)
                            for k in current_parameter
                        ]
                        up_proj = torch.cat(up_proj, dim=-1)

                        gate_up_proj = torch.cat((gate_proj, up_proj), dim=-1)
                        new_key = new_key.replace("up_proj", "gate_up_proj")
                        state_dict[new_key] = gate_up_proj.contiguous()

                    tqdm.write(f"Processing: {key.ljust(50)}  ->\t {new_key}, {state_dict[new_key].shape}")
            elif "down_proj" in new_key:
                current_parameter = torch.cat(current_parameter, dim=concat_dim)
                if "experts" in new_key:
                    p = []
                    for i in range(8):
                        p += [current_parameter.reshape(8, -1, 5120)[i, :, :].view(num_experts, -1, 5120)]
                    current_parameter = torch.cat(p, dim=1)
                state_dict[new_key] = current_parameter.contiguous()
                tqdm.write(f"Processing: {key.ljust(50)}  ->\t {new_key}, {state_dict[new_key].shape}")
            elif "router" in new_key:
                current_parameter = torch.cat(current_parameter, dim=concat_dim)
                state_dict[new_key] = current_parameter.transpose(0, 1)
            elif "lm_head" in new_key:
                current_parameter = torch.cat(current_parameter, dim=concat_dim).clone()
                # TODO we need to do better than mean, works for now
                # if (vocab_size - current_parameter.shape[0]) > 0:
                #     mean_embedding = torch.mean(current_parameter, dim=0)[:, None].repeat(vocab_size-current_parameter.shape[0],1)
                #     print(mean_embedding.shape)
                #     current_parameter = torch.cat((current_parameter, mean_embedding), dim=0)
                state_dict[new_key] = current_parameter
                tqdm.write(
                    f"Processing: {key.ljust(50)}  ->\t {new_key}, {state_dict[new_key].shape}, concat dim = {concat_dim}"
                )
            elif new_key == "vision_model.patch_embedding.linear.weight":
                current_parameter = torch.cat(current_parameter, dim=concat_dim).clone()
                # We don't reshape the patch embedding as we're using unfolded convolution as well
                state_dict[new_key] = current_parameter  # .reshape(-1, 3, vision_patch_size, vision_patch_size)
            # generic concat for weights/select one for biases
            elif isinstance(current_parameter, list) and len(current_parameter) > 0:
                if not is_param_same_across_shards(new_key):
                    current_parameter = torch.cat(current_parameter, dim=concat_dim)
                    state_dict[new_key] = current_parameter
                    tqdm.write(
                        f"Processing: {key.ljust(50)}  ->\t {new_key}, {state_dict[new_key].shape}, concat dim = {concat_dim}"
                    )
                elif is_param_same_across_shards(new_key):
                    state_dict[new_key] = current_parameter[0]
                    tqdm.write(
                        f"Processing: {key.ljust(50)}  ->\t {new_key}, {state_dict[new_key].shape}, concat dim = {concat_dim}"
                    )

            elif new_key == "":
                # skip empty keys
                continue
            else:
                # just load the parameter
                state_dict[new_key] = current_parameter
                tqdm.write(
                    f"Processing: {key.ljust(50)}  ->\t {new_key}, {state_dict[new_key].shape}, concat dim = {concat_dim}"
                )
        del loaded
        gc.collect()

        print("Loading the checkpoint in a Llama4 model.")
        state_dict.pop("")
        model.load_state_dict(state_dict, strict=True, assign=True)
        print("Model reloaded successfully.")
        print("Saving the model.")
        model.save_pretrained(model_path)
        del state_dict, model

        # Safety check: reload the converted model
        gc.collect()
    print("Reloading the model to check if it's saved correctly.")
    with torch.no_grad():
        # TODO test if we can do `tp_plan="auto"``
        model = Llama4ForConditionalGeneration.from_pretrained(
            model_path, dtype=torch.bfloat16, device_map="auto", attn_implementation="eager"
        )

        model.generation_config.top_p = 0.9
        model.generation_config.temperature = 0.6
        print("Model reloaded successfully.")

        from transformers import AutoTokenizer

        tokenizer = AutoTokenizer.from_pretrained(model_path)
        inputs = tokenizer(["Roses are red,"], return_tensors="pt").to(model.device)
        out = model.generate(**inputs, max_new_tokens=4)
        print(tokenizer.batch_decode(out))
    # generation config
    if instruct:
        print("Saving generation config...")
        generation_config = GenerationConfig(
            do_sample=True,
            temperature=0.6,
            top_p=0.9,
            bos_token_id=bos_token_id,
            eos_token_id=eos_token_id,
            pad_token_id=pad_token_id,
        )
        generation_config.save_pretrained(model_path)