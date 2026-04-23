def write_model(save_path, input_base_path, config, push_to_hub=False, dtype=torch.float32):
    print(f"Fetching all parameters from the checkpoint at '{input_base_path}'")
    model_state_dict = torch.load(input_base_path, map_location="cpu", weights_only=True)

    REPLACEMENT = {
        "blocks.": "layers.",
        ".ffw_down.b": ".down_proj.b",
        ".ffw_down.w": ".down_proj.w",
        ".ffw_up.b": ".up_proj.bias",
        ".ffw_up.w": ".up_proj.weight",
        "recurrent_block": "temporal_block",
        "attention_block": "temporal_block",
        "temporal_block.proj_final": "temporal_block.out_proj",
        "norm.scale": "norm.weight",
        ".proj_k": ".k_proj",
        ".proj_q": ".q_proj",
        ".proj_v": ".v_proj",
        ".proj_final": ".o_proj",
        "embedder.input_embedding": "embed_tokens.weight",
        "conv_1d.w": "conv_1d.weight",
        "conv_1d.b": "conv_1d.bias",
        "input_gate.w": "input_gate.weight",
        "input_gate.b": "input_gate.bias",
        "a_param": "recurrent_param",
        "a_gate.b": "recurrent_gate.bias",
        "a_gate.w": "recurrent_gate.weight",
    }

    state_dict = {}
    for k, v in model_state_dict.items():
        k = "model." + k
        pattern = re.compile("|".join(map(re.escape, REPLACEMENT.keys())))
        key = pattern.sub(lambda match: REPLACEMENT[match.group(0)], k)
        if "conv_1d.weight" in key:
            v = v[:, None, :].transpose(0, 2)
        if "up_proj.weight" in key:
            state_dict[key.replace("up_proj", "gate_proj")] = v[0].T.contiguous()
            v = v[1].T.contiguous()
        if "up_proj.bias" in key:
            state_dict[key.replace("up_proj", "gate_proj")] = v[0, 0, 0].clone()
            v = v[1, 0, 0].contiguous()
        if "recurrent_gate.bias" in key:
            state_dict[key.replace("gate.", "gate_")] = v.contiguous().clone()
        elif "recurrent_gate.weight" in key:
            state_dict[key.replace("gate.", "gate_")] = v.contiguous().clone()
        elif "input_gate.b" in key:
            state_dict[key.replace("gate.", "gate_")] = v.contiguous().clone()
        elif "input_gate.w" in key:
            state_dict[key.replace("gate.", "gate_")] = v.contiguous().clone()
        elif "embed_tokens" in key:
            state_dict[key] = v[: config.vocab_size, :].contiguous().clone()
            state_dict["lm_head.weight"] = v[: config.vocab_size, :].contiguous().clone()
        else:
            state_dict[key] = v.contiguous()

    torch.set_default_dtype(dtype)

    print("Loading the checkpoint in a Gemma model.")
    with torch.device("meta"):
        model = RecurrentGemmaForCausalLM(config)
    model.load_state_dict(state_dict, assign=True, strict=True)

    model.config.dtype = torch.float32
    del model.config._name_or_path
    print("Saving in the Transformers format.")

    if push_to_hub:
        print(f"pushing the model to {save_path}")
    else:
        model.save_pretrained(save_path)