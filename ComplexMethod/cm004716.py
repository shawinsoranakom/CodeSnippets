def write_model(model_name, pretrained_model_weights_path, pytorch_dump_folder_path, push_to_hub):
    # load modified config. Why? After loading the default config, the backbone kwargs are already set.
    if "dc5" in model_name:
        config = DabDetrConfig(dilation=True)
    else:
        # load default config
        config = DabDetrConfig()
    # set other attributes
    if model_name == "dab-detr-resnet-50-dc5":
        config.temperature_height = 10
        config.temperature_width = 10
    if "fixxy" in model_name:
        config.random_refpoints_xy = True
    if "pat3" in model_name:
        config.num_patterns = 3
        # only when the number of patterns (num_patterns parameter in config) are more than 0 like r50-pat3 or r50dc5-pat3
        ORIGINAL_TO_CONVERTED_KEY_MAPPING.update({r"transformer.patterns.weight": r"patterns.weight"})

    config.num_labels = 91
    repo_id = "huggingface/label-files"
    filename = "coco-detection-id2label.json"
    id2label = json.load(open(hf_hub_download(repo_id, filename, repo_type="dataset"), "r"))
    id2label = {int(k): v for k, v in id2label.items()}
    config.id2label = id2label
    config.label2id = {v: k for k, v in id2label.items()}
    # load original model from local path
    loaded = torch.load(pretrained_model_weights_path, map_location=torch.device("cpu"), weights_only=True)["model"]
    # Renaming the original model state dictionary to HF compatible
    all_keys = list(loaded.keys())
    new_keys = convert_old_keys_to_new_keys(all_keys)
    state_dict = {}
    for key in all_keys:
        if "backbone.0.body" in key:
            new_key = key.replace("backbone.0.body", "backbone.conv_encoder.model._backbone")
            state_dict[new_key] = loaded[key]
        # Q, K, V encoder values mapping
        elif re.search("self_attn.in_proj_(weight|bias)", key):
            # Dynamically find the layer number
            pattern = r"layers\.(\d+)\.self_attn\.in_proj_(weight|bias)"
            match = re.search(pattern, key)
            if match:
                layer_num = match.group(1)
            else:
                raise ValueError(f"Pattern not found in key: {key}")

            in_proj_value = loaded.pop(key)
            if "weight" in key:
                state_dict[f"encoder.layers.{layer_num}.self_attn.q_proj.weight"] = in_proj_value[:256, :]
                state_dict[f"encoder.layers.{layer_num}.self_attn.k_proj.weight"] = in_proj_value[256:512, :]
                state_dict[f"encoder.layers.{layer_num}.self_attn.v_proj.weight"] = in_proj_value[-256:, :]
            elif "bias" in key:
                state_dict[f"encoder.layers.{layer_num}.self_attn.q_proj.bias"] = in_proj_value[:256]
                state_dict[f"encoder.layers.{layer_num}.self_attn.k_proj.bias"] = in_proj_value[256:512]
                state_dict[f"encoder.layers.{layer_num}.self_attn.v_proj.bias"] = in_proj_value[-256:]
        else:
            new_key = new_keys[key]
            state_dict[new_key] = loaded[key]

    del loaded
    gc.collect()
    # important: we need to prepend a prefix to each of the base model keys as the head models use different attributes for them
    prefix = "model."
    for key in state_dict.copy():
        if not key.startswith("class_embed") and not key.startswith("bbox_predictor"):
            val = state_dict.pop(key)
            state_dict[prefix + key] = val
    # finally, create HuggingFace model and load state dict
    model = DabDetrForObjectDetection(config)
    model.load_state_dict(state_dict)
    model.eval()
    logger.info(f"Saving PyTorch model to {pytorch_dump_folder_path}...")
    Path(pytorch_dump_folder_path).mkdir(exist_ok=True)
    model.save_pretrained(pytorch_dump_folder_path)

    if push_to_hub:
        model.push_to_hub(repo_id=model_name, commit_message="Add new model")