def write_model(save_path, input_base_path, config, push_to_hub=False, dtype=torch.float32):
    num_attn_heads = config.num_attention_heads
    hidden_size = config.hidden_size
    num_kv_heads = config.num_key_value_heads
    head_dim = config.head_dim

    print(f"Fetching all parameters from the checkpoint at '{input_base_path}'")

    if os.path.isdir(input_base_path):
        print("Model seems sharded")

        model_state_dict = {}
        files = [file for file in os.listdir(input_base_path) if file.endswith(".bin")]

        for file in files:
            print(file)
            loaded_state_dict = torch.load(os.path.join(input_base_path, file), map_location="cpu", weights_only=True)
            model_state_dict.update(loaded_state_dict)
    else:
        print("Model does not seem to be sharded")
        model_state_dict = torch.load(input_base_path, map_location="cpu", weights_only=True)["model_state_dict"]
        model_state_dict.pop("freqs_cis")

    state_dict = {}
    for k, v in model_state_dict.items():
        if "qkv_proj" in k:
            if num_kv_heads == 1:
                v = v.reshape(num_attn_heads + num_kv_heads * 2, head_dim, hidden_size)
                q_proj = v[:num_attn_heads, ...]
                k_proj = v[num_attn_heads : num_attn_heads + num_kv_heads, ...].repeat(num_kv_heads, 1, 1)
                v_proj = v[-num_kv_heads:, ...].repeat(num_kv_heads, 1, 1)

                state_dict[k.replace("qkv_proj", "q_proj")] = q_proj.reshape(
                    num_attn_heads * head_dim, hidden_size
                ).clone()
                state_dict[k.replace("qkv_proj", "k_proj")] = k_proj.reshape(
                    num_kv_heads * head_dim, hidden_size
                ).clone()
                state_dict[k.replace("qkv_proj", "v_proj")] = v_proj[0].clone()
            else:
                q_proj, k_proj, v_proj = torch.split(
                    v, [num_attn_heads * head_dim, num_kv_heads * head_dim, num_kv_heads * head_dim], 0
                )
                state_dict[k.replace("qkv_proj", "q_proj")] = q_proj.reshape(
                    num_attn_heads * head_dim, hidden_size
                ).clone()
                state_dict[k.replace("qkv_proj", "k_proj")] = k_proj.reshape(
                    num_kv_heads * head_dim, hidden_size
                ).clone()
                state_dict[k.replace("qkv_proj", "v_proj")] = v_proj.reshape(
                    num_kv_heads * head_dim, hidden_size
                ).clone()

        elif k == "embedder.weight":
            state_dict[LAYER_NAME_MAPPING[k]] = v
            state_dict["lm_head.weight"] = v
        else:
            state_dict[k] = v

    torch.set_default_dtype(dtype)

    print("Loading the checkpoint in a Gemma2 model.")
    with torch.device("meta"):
        model = Gemma2ForCausalLM(config)
    model.load_state_dict(state_dict, assign=True, strict=False)

    model.config.dtype = torch.float32
    del model.config._name_or_path
    print("Saving in the Transformers format.")

    if push_to_hub:
        print(f"pushing the model to {save_path}")
        model.push_to_hub(save_path, private=True)
    else:
        model.save_pretrained(save_path)