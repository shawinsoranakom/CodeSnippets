def write_model(
    model_path,
    input_base_path,
    num_shards,
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
    text_vocab_size = params["vocab_size"]
    text_num_layers = params["n_layers"]
    text_dim = params["dim"]
    text_num_heads = params["n_heads"]
    text_rms_norm_eps = params["norm_eps"]
    text_rope_theta = params["rope_theta"]
    cross_attention_num_layers = params["vision_num_cross_attention_layers"]

    # some constants from original code
    rope_parameters = {
        "rope_type": "llama3",
        "factor": 8.0,
        "low_freq_factor": 1.0,
        "high_freq_factor": 4.0,
        "original_max_position_embeddings": 8192,
    }
    max_position_embeddings = CONTEXT_LENGTH

    # compute additional params for weight conversion
    text_num_heads_per_shard = text_num_heads // num_shards
    text_dim_per_head = text_dim // text_num_heads
    text_intermediate_size = compute_intermediate_size(text_dim, multiple_of=params["multiple_of"])

    if params.get("n_kv_heads", None) is not None:
        text_num_key_value_heads = params["n_kv_heads"]  # for GQA / MQA
        text_num_key_value_heads_per_shard = text_num_key_value_heads // num_shards
        text_key_value_dim = text_dim_per_head * text_num_key_value_heads
    else:  # compatibility with other checkpoints
        text_num_key_value_heads = text_num_heads
        text_num_key_value_heads_per_shard = text_num_heads_per_shard
        text_key_value_dim = text_dim

    # cross-attention layers: 20 for 90B, 8 for 11B
    cross_attention_frequency = math.ceil(text_num_layers / cross_attention_num_layers)
    text_num_total_layers = text_num_layers + cross_attention_num_layers
    cross_attention_layers_shift = list(
        range(cross_attention_frequency - 1, text_num_total_layers, cross_attention_frequency + 1)
    )
    self_attention_layers_shift = [k for k in range(text_num_total_layers) if k not in cross_attention_layers_shift]

    bos_token_id = 128000
    eos_token_id = [128001, 128008, 128009] if instruct else 128001
    pad_token_id = 128004

    text_config = MllamaTextConfig(
        num_attention_heads=text_num_heads,
        vocab_size=text_vocab_size,
        hidden_size=text_dim,
        rms_norm_eps=text_rms_norm_eps,
        rope_theta=text_rope_theta,
        num_hidden_layers=text_num_total_layers,
        cross_attention_layers=cross_attention_layers_shift,
        intermediate_size=text_intermediate_size,
        max_position_embeddings=max_position_embeddings,
        rope_parameters=rope_parameters,
        bos_token_id=bos_token_id,
        eos_token_id=eos_token_id,
        pad_token_id=pad_token_id,
        tie_word_embeddings=False,  # Constant set to False
        dtype=dtype,
    )

    # ------------------------------------------------------------
    # Vision model params and config
    # ------------------------------------------------------------

    # params from config
    vision_tile_size = params["vision_chunk_size"]
    vision_max_num_tiles = params["vision_max_num_chunks"]

    # some constants from original code
    vision_patch_size = 14
    vision_num_channels = 3
    vision_num_layers = 32
    vision_num_layers_global = 8
    vision_dim = 1280
    vision_num_heads = 16
    vision_intermediate_layers_indices = [3, 7, 15, 23, 30]

    # compute additional params for weight conversion
    vision_dim_per_head = vision_dim // vision_num_heads
    vision_num_heads_per_shard = vision_num_heads // num_shards
    vision_intermediate_size = vision_dim * 4
    vision_supported_aspect_ratios = get_all_supported_aspect_ratios(vision_max_num_tiles)

    vision_config = MllamaVisionConfig(
        hidden_size=vision_dim,
        patch_size=vision_patch_size,
        num_channels=vision_num_channels,
        intermediate_size=vision_intermediate_size,
        num_hidden_layers=vision_num_layers,
        num_attention_heads=vision_num_heads,
        num_global_layers=vision_num_layers_global,
        intermediate_layers_indices=vision_intermediate_layers_indices,
        image_size=vision_tile_size,
        max_num_tiles=vision_max_num_tiles,
        supported_aspect_ratios=vision_supported_aspect_ratios,
        dtype=dtype,
    )

    # save config
    config = MllamaConfig(vision_config=vision_config, text_config=text_config, dtype=dtype)
    config.architectures = ["MllamaForConditionalGeneration"]
    config.save_pretrained(model_path)
    print("Model config saved successfully...")

    # ------------------------------------------------------------
    # Convert weights
    # ------------------------------------------------------------

    print(f"Fetching all parameters from the checkpoint at {input_base_path}...")
    if num_shards == 1:
        if os.path.exists(os.path.join(input_base_path, "consolidated.00.pth")):
            path = os.path.join(input_base_path, "consolidated.00.pth")
        else:
            path = os.path.join(input_base_path, "consolidated.pth")
        loaded = [torch.load(path, map_location="cpu", mmap=True, weights_only=True)]
    else:
        loaded = [
            torch.load(
                os.path.join(input_base_path, f"consolidated.{i:02d}.pth"),
                map_location="cpu",
                mmap=True,
                weights_only=True,
            )
            for i in range(num_shards)
        ]

    print("Converting model...")
    all_keys = list(loaded[0].keys())
    new_keys = convert_old_keys_to_new_keys(all_keys)

    state_dict = {}
    for key in all_keys:
        new_key = new_keys[key]

        # In the original model, self-attention layers and cross-attention layers are different lists of layers.
        # In the converted model, they are merged into one list with corresponding index shift to preserve the order.
        if ("cross_attention" in key or "text_model.layers" in key) and "language_model" in new_key:
            shift = cross_attention_layers_shift if "cross_attention" in key else self_attention_layers_shift
            new_key = re.sub(r"layers.(\d+).", lambda _match: f"layers.{shift[int(_match.groups()[0])]}.", new_key)

        current_parameter = [chunk.pop(key).contiguous().clone() for chunk in loaded]
        if not is_param_different_across_shards(new_key):
            current_parameter = current_parameter[0]

        concat_dim = get_concat_dim(new_key)

        # Post-process the current_parameter.
        if re.search("(k|v|q)_proj.weight", new_key) and "language_model" in new_key:
            if "q_proj" in new_key:
                param_num_heads = text_num_heads
                param_num_head_per_shard = text_num_heads_per_shard
                param_dim = text_dim
            else:
                param_num_heads = text_num_key_value_heads
                param_num_head_per_shard = text_num_key_value_heads_per_shard
                param_dim = text_key_value_dim
            shards = [param.view(param_num_head_per_shard, text_dim_per_head, text_dim) for param in current_parameter]
            current_parameter = torch.cat(shards, dim=concat_dim)
            if "cross_attn" not in new_key and "v_proj.weight" not in new_key:
                current_parameter = permute_for_rope(current_parameter, param_num_heads, param_dim, text_dim)
            state_dict[new_key] = current_parameter.reshape(param_num_heads * text_dim_per_head, text_dim)

        elif "vision_model" in new_key and re.search("(k|v|q)_proj", new_key):
            shards = [
                param.view(vision_num_heads_per_shard, vision_dim_per_head, vision_dim) for param in current_parameter
            ]
            param = torch.cat(shards, dim=concat_dim)
            state_dict[new_key] = param.reshape(vision_num_heads * vision_dim_per_head, vision_dim)

        elif new_key == "vision_model.patch_embedding.weight":
            current_parameter = torch.cat(current_parameter, dim=concat_dim)
            state_dict[new_key] = current_parameter.reshape(
                -1, vision_num_channels, vision_patch_size, vision_patch_size
            )

        elif new_key.endswith("gate"):
            state_dict[new_key] = current_parameter[0].view(1)

        elif "vision_model.gated_positional_embedding.embedding" in new_key:
            current_parameter = interpolate_positional_embedding(
                current_parameter, vision_tile_size, vision_patch_size
            )
            state_dict[new_key] = current_parameter

        elif "vision_model.gated_positional_embedding.tile_embedding.weight" in new_key:
            current_parameter = current_parameter.permute(2, 0, 1, 3).flatten(1)
            current_parameter = interpolate_positional_embedding(
                current_parameter, vision_tile_size, vision_patch_size
            )
            current_parameter = current_parameter.reshape(
                -1, vision_max_num_tiles, vision_max_num_tiles, vision_dim
            ).permute(1, 2, 0, 3)
            state_dict[new_key] = pre_compute_positional_embedding(current_parameter)

        elif "tile_positional_embedding.embedding" in new_key:
            state_dict[new_key] = pre_compute_positional_embedding(current_parameter)

        elif new_key != "":
            if isinstance(current_parameter, list):
                current_parameter = torch.cat(current_parameter, dim=concat_dim)
            state_dict[new_key] = current_parameter

    state_dict["language_model.model.embed_tokens.weight"] = torch.cat(
        [
            state_dict["language_model.model.embed_tokens.weight"],
            state_dict.pop("language_model.model.learnable_embedding.weight"),
        ],
        dim=0,
    )
    del loaded
    gc.collect()

    print("Loading the checkpoint in a Mllama model.")
    with torch.device("meta"):
        model = MllamaForConditionalGeneration(config)
    model.load_state_dict(state_dict, strict=True, assign=True)
    print("Checkpoint loaded successfully.")
    del model.config._name_or_path

    print("Saving the model.")
    model.save_pretrained(model_path)
    del state_dict, model

    # Safety check: reload the converted model
    gc.collect()
    print("Reloading the model to check if it's saved correctly.")
    MllamaForConditionalGeneration.from_pretrained(model_path, dtype=torch.bfloat16, device_map="auto")
    print("Model reloaded successfully.")

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