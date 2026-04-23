def write_model(
    model_path,
    input_base_path,
    push_to_hub=False,
    hub_dir=None,
):
    os.makedirs(model_path, exist_ok=True)

    config = get_internvl_config(input_base_path)
    config.architectures = ["InternVLForConditionalGeneration"]
    config.save_pretrained(model_path)
    if push_to_hub:
        model_name = (hub_dir or model_path).split(os.path.sep)[-1]
        config.push_to_hub(model_name)
    print("Model config saved successfully...")

    # ------------------------------------------------------------
    # Convert weights
    # ------------------------------------------------------------

    print(f"Fetching all parameters from the checkpoint at {input_base_path}...")
    state_dict_old = load_original_state_dict(input_base_path)
    print("Converting model...")
    all_keys = list(state_dict_old.keys())
    new_keys = convert_old_keys_to_new_keys(all_keys, path=input_base_path)
    lm_dim = config.text_config.hidden_size
    dim = config.vision_config.hidden_size
    state_dict = {}
    for key in all_keys:
        new_key = new_keys[key]
        if "attn.qkv" in key:
            new_key_query = new_key.replace("attention.qkv", "attention.q_proj")
            state_dict[new_key_query] = state_dict_old[key][:dim]

            new_key_key = new_key.replace("attention.qkv", "attention.k_proj")
            state_dict[new_key_key] = state_dict_old[key][dim : 2 * dim]

            new_key_value = new_key.replace("attention.qkv", "attention.v_proj")
            state_dict[new_key_value] = state_dict_old[key][-dim:]
        elif "attention.wqkv" in key:
            num_key_value_groups = config.text_config.num_attention_heads // config.text_config.num_key_value_heads
            head_dim = config.text_config.head_dim
            wqkv_weights = state_dict_old[key]

            qkv_vecs = rearrange(wqkv_weights, "(h gs d) z -> h gs d z", gs=2 + num_key_value_groups, d=head_dim)
            q_proj = qkv_vecs[:, :num_key_value_groups, ...].reshape(-1, lm_dim).contiguous()
            k_proj = qkv_vecs[:, -2, ...].reshape(-1, lm_dim).contiguous()
            v_proj = qkv_vecs[:, -1, ...].reshape(-1, lm_dim).contiguous()

            new_key_query = new_key.replace("attention.wqkv", "self_attn.q_proj")
            state_dict[new_key_query] = q_proj

            new_key_key = new_key.replace("attention.wqkv", "self_attn.k_proj")
            state_dict[new_key_key] = k_proj

            new_key_value = new_key.replace("attention.wqkv", "self_attn.v_proj")
            state_dict[new_key_value] = v_proj
        else:
            state_dict[new_key] = state_dict_old[key]

    del state_dict_old
    gc.collect()

    print("Loading the checkpoint in a InternVLForConditionalGeneration model.")
    model = InternVLForConditionalGeneration(config)
    missing_keys, unexpected_keys = model.load_state_dict(state_dict, strict=False)
    model = model.to(torch.bfloat16)
    print("model dtype:", model.dtype)
    print("Missing keys:", missing_keys)
    print("Unexpected keys:", unexpected_keys)

    print("Saving the model.")
    model_name = model_path.split(os.path.sep)[-1]
    model.save_pretrained(model_path)
    if push_to_hub:
        model.push_to_hub(model_name)

    image_processor = GotOcr2ImageProcessor.from_pretrained(model_path)
    video_processor = InternVLVideoProcessor.from_pretrained(model_path)
    tokenizer = AutoTokenizer.from_pretrained(model_path)
    processor = InternVLProcessor(
        image_processor=image_processor,
        video_processor=video_processor,
        tokenizer=tokenizer,
        chat_template=chat_template,
    )
    processor.save_pretrained(model_path)
    if push_to_hub:
        processor.push_to_hub(model_name)

    # generation config
    if get_lm_type(input_base_path) == "llama":
        print("Saving generation config...")
        # in the original model, eos_token is not the same in the text_config and the generation_config
        # ("</s>" - 2 in the text_config and "<|im_end|>" - 92542 in the generation_config)
        generation_config = GenerationConfig(
            eos_token_id=92542,
        )
        generation_config.save_pretrained(model_path)
        if push_to_hub:
            generation_config.push_to_hub(model_name)

    # del state_dict, model

    # # Safety check: reload the converted model
    gc.collect()
    print("Reloading the model to check if it's saved correctly.")
    model = InternVLForConditionalGeneration.from_pretrained(model_path, device_map="auto", dtype=torch.bfloat16)
    print("Model reloaded successfully.")
    del model