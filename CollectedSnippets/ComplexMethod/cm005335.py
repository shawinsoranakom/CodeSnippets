def merge_tp_weights(model_path, output_path, vllm_config_path=None):
    origin_tp, origin_ep, origin_pp = -1, -1, -1

    check_ep_or_pp_later = False
    for item in Path(model_path).iterdir():
        if item.is_dir():
            match = re.match(r"mp_rank_(\d{2})(?:_(\d{3}))?(?:_(\d{3}))?", item.name)
            if match:
                groups = match.groups()
                tp = int(groups[0])
                origin_tp = max(origin_tp, tp + 1)
                # maybe TP-EP or TP-PP, need check later
                if groups[1] is not None and groups[2] is None:
                    pp = int(groups[1])
                    origin_pp = max(origin_pp, pp + 1)
                    origin_ep = 1
                    check_ep_or_pp_later = True
                elif groups[1] is not None and groups[2] is not None:
                    pp = int(groups[1])
                    ep = int(groups[2])
                    origin_pp = max(origin_pp, pp + 1)
                    origin_ep = max(origin_ep, ep + 1)
                else:
                    origin_ep = 1
                    origin_pp = 1

    tensor_names_by_file = {}
    mgt_sd = {}
    for item in Path(model_path).iterdir():
        if item.is_dir():
            match = re.match(r"mp_rank_(\d{2})(?:_(\d{3}))?(?:_(\d{3}))?$", item.name)
            if match:
                groups = match.groups()
                tp = int(groups[0])
                pp = int(groups[1]) if groups[1] is not None else 0
                ep = int(groups[2]) if groups[2] is not None else 0

                file_path = item / "model_optim_rng.pt"
                assert file_path.exists(), f"model_optim_rng.pt not found in {item}"

                file_sd = torch.load(file_path, map_location="cpu", weights_only=False)

                for k in list(file_sd.keys()):
                    if "_extra_state" in k or "dummy_parameter" in k:
                        file_sd.pop(k)

                mgt_sd[(tp, pp, ep)] = file_sd

                tensor_names = set()
                if "model" in file_sd:
                    for key in file_sd["model"].keys():
                        tensor_names.add(key)
                tensor_names_by_file[(tp, pp, ep)] = tensor_names

    change_pp_to_ep = False
    if check_ep_or_pp_later:
        prefix_distribution = {}

        for (tp, pp, ep), prefixes in tensor_names_by_file.items():
            for prefix in prefixes:
                if prefix not in prefix_distribution:
                    prefix_distribution[prefix] = set()
                prefix_distribution[prefix].add((tp, pp, ep))

        for prefix, locations in prefix_distribution.items():
            if len(locations) > 1:
                pp_values = {loc[1] for loc in locations}
                if len(pp_values) > 1:
                    print(f"find '{prefix}' in multi ranks {pp_values} the parallelism should be TP-EP")
                    origin_ep = origin_pp
                    origin_pp = 1
                    change_pp_to_ep = True
                    break
                else:
                    print(f"find '{prefix}' only in one ep, parallelism should be TP-PP")
                    break

    print(f"Detected tensor parallel degree TP={origin_tp} EP={origin_ep} PP={origin_pp}")
    assert max(origin_tp, origin_ep) * origin_pp == len(tensor_names_by_file), "maybe some problem in origin weight"

    organized_sd = {}
    for (tp, pp, ep), file_sd in mgt_sd.items():
        if change_pp_to_ep:
            pp, ep = ep, pp
        organized_sd.setdefault(pp, {})
        organized_sd[pp][(ep, tp)] = file_sd
        find_vpp = "model0" in file_sd

    # support VPP, if each pp rank has n vpp blocks, we will treat the original model
    # was parallel as pp n * origin_pp
    if find_vpp:
        organized_sd_vpp = {}
        for i in range(origin_pp):
            for (ep, tp), file_sd in organized_sd[i].items():
                model_keys = sorted(
                    [key for key in file_sd.keys() if key.startswith("model") and key[5:].isdigit()],
                    key=lambda x: int(x[5:]),
                )
                vp_blocks = len(model_keys)
                for idx, key in enumerate(model_keys):
                    assert key in file_sd, f"model {key} not found"
                    organized_sd_vpp.setdefault(idx * origin_pp + i, {})
                    organized_sd_vpp[idx * origin_pp + i][(ep, tp)] = {"model": file_sd[key]}
        origin_pp = origin_pp * vp_blocks
        organized_sd = organized_sd_vpp

    ignore_list = ["_extra_state", "dummy_parameter"]
    layer_share_list = [
        "norm",
        "conv3d",
        "downsample",
        "router",
        "mlp.linear_fc2.bias",
        "self_attention.linear_proj.bias",
        "position_embeddings",
    ]

    full_weights = {}

    vit_layer_offset = 0
    llm_layer_offset = 0
    llm_layer_pattern = re.compile(r"^(decoder\.layers\.)(\d+)(\..*)$")
    vit_layer_pattern = re.compile(r"^(vision_model\.transformer\.layers\.)(\d+)(\..*)$")
    for pp in sorted(organized_sd.keys()):
        pp_dict = organized_sd[pp]
        next_llm_layer_offset = llm_layer_offset
        next_vit_layer_offset = vit_layer_offset
        ep_map = {}
        tp_map = {}
        tp_seen = set()
        for (ep, tp), item in pp_dict.items():
            if tp not in tp_seen:
                tp_seen.add(tp)
                tp_map[tp] = item
            ep_map[ep] = item

        for tp in sorted(tp_map.keys()):
            sd = tp_map[tp]
            for full_name, tensor in sd["model"].items():
                if any(x in full_name for x in ignore_list):
                    continue
                llm_name_match = llm_layer_pattern.match(full_name)
                if llm_name_match:
                    # Use a closure to avoid global variable issues
                    def offset_layer(x, offset=llm_layer_offset):
                        nonlocal next_llm_layer_offset
                        _real_layer = int(x.group(2)) + offset
                        next_llm_layer_offset = max(next_llm_layer_offset, _real_layer + 1)
                        return f"{x.group(1)}{_real_layer}{x.group(3)}"

                    full_name = llm_layer_pattern.sub(offset_layer, full_name)
                vit_name_match = vit_layer_pattern.match(full_name)
                if vit_name_match:
                    # Use a closure to avoid global variable issues
                    def offset_layer(x, offset=vit_layer_offset):
                        nonlocal next_vit_layer_offset
                        _real_layer = int(x.group(2)) + offset
                        next_vit_layer_offset = max(next_vit_layer_offset, _real_layer + 1)
                        return f"{x.group(1)}{_real_layer}{x.group(3)}"

                    full_name = vit_layer_pattern.sub(offset_layer, full_name)
                if layer_share_list and any(x in full_name for x in layer_share_list):
                    if full_name not in full_weights:
                        full_weights[full_name] = tensor
                    else:
                        assert torch.equal(tensor, full_weights[full_name]), (
                            f"detect diff param in tp named: {full_name}"
                        )
                elif not re.search(r"\.experts\.", full_name):
                    full_weights.setdefault(full_name, [None for _ in range(origin_tp)])
                    full_weights[full_name][tp] = tensor

        for ep in sorted(ep_map.keys()):
            sd = ep_map[ep]
            for full_name, tensor in sd["model"].items():
                if any(x in full_name for x in ignore_list):
                    continue
                name_match = llm_layer_pattern.match(full_name)
                if name_match:
                    # Use a closure to avoid global variable issues
                    def offset_layer(x, offset=llm_layer_offset):
                        nonlocal next_llm_layer_offset
                        _real_layer = int(x.group(2)) + offset
                        next_llm_layer_offset = max(next_llm_layer_offset, _real_layer + 1)
                        return f"{x.group(1)}{_real_layer}{x.group(3)}"

                    full_name = llm_layer_pattern.sub(offset_layer, full_name)
                if re.search(r"\.experts\.", full_name):
                    full_weights.setdefault(full_name, [None for _ in range(origin_ep)])
                    full_weights[full_name][ep] = tensor
        llm_layer_offset = next_llm_layer_offset
        vit_layer_offset = next_vit_layer_offset

    for k in sorted(full_weights.keys()):
        item = full_weights[k]
        if isinstance(item, list):
            print(f"{k} {len(item)} {item[0].shape} {item[0].dtype}", flush=True)
        else:
            print(f"{k} {item.shape} {item.dtype}", flush=True)

    print(f"Loading vLLM configuration file: {vllm_config_path}")
    with open(vllm_config_path, "r") as f:
        model_config = json.load(f)
        text_config = model_config.get("text_config", {})
        vision_config = model_config.get("vision_config", {})

        num_layers = text_config.get("num_hidden_layers", 40)
        num_heads = text_config.get("num_attention_heads", 32)
        num_kv_heads = text_config.get("num_key_value_heads", 2)
        hidden_size = model_config.get("hidden_size", 4096)
        head_dim = model_config.get("attention_dim", hidden_size // num_heads)
        vision_num_layers = vision_config.get("depth", 24)
        vit_n_head = vision_config.get("num_heads", 12)

    print(
        f"Model parameters: num_layers={num_layers}, vision_num_layers={vision_num_layers}, "
        f"num_heads={num_heads}, multi_query_group_num={num_kv_heads}"
    )

    print("Merging tensor parallel weights...")

    interleaved_qkv = True
    num_attention_heads = num_heads
    multi_query_group_num = num_kv_heads
    attention_dim = head_dim
    complete_state_dict = {}

    # LLM
    layer_i = 0
    while f"decoder.layers.{layer_i}.self_attention.linear_qkv.layer_norm_weight" in full_weights:
        if f"decoder.layers.{layer_i}.self_attention.linear_qkv.layer_norm_weight" in full_weights:
            complete_state_dict[f"model.language_model.layers.{layer_i}.input_layernorm.weight"] = full_weights[
                f"decoder.layers.{layer_i}.self_attention.linear_qkv.layer_norm_weight"
            ]

        if f"decoder.layers.{layer_i}.pre_mlp_layernorm.weight" in full_weights:
            complete_state_dict[f"model.language_model.layers.{layer_i}.post_attention_layernorm.weight"] = (
                full_weights[f"decoder.layers.{layer_i}.pre_mlp_layernorm.weight"]
            )
        elif f"decoder.layers.{layer_i}.mlp.linear_fc1.layer_norm_weight" in full_weights:
            complete_state_dict[f"model.language_model.layers.{layer_i}.post_attention_layernorm.weight"] = (
                full_weights[f"decoder.layers.{layer_i}.mlp.linear_fc1.layer_norm_weight"]
            )

        # GLM-4.1V Only
        if f"decoder.layers.{layer_i}.post_mlp_layernorm.weight" in full_weights:
            complete_state_dict[f"model.language_model.layers.{layer_i}.post_mlp_layernorm.weight"] = full_weights[
                f"decoder.layers.{layer_i}.post_mlp_layernorm.weight"
            ]

        if f"decoder.layers.{layer_i}.post_self_attn_layernorm.weight" in full_weights:
            complete_state_dict[f"model.language_model.layers.{layer_i}.post_self_attn_layernorm.weight"] = (
                full_weights[f"decoder.layers.{layer_i}.post_self_attn_layernorm.weight"]
            )

        q, k, v = merge_qkv(
            sd_list=full_weights[f"decoder.layers.{layer_i}.self_attention.linear_qkv.weight"],
            original_tp=origin_tp,
            num_attention_heads=num_attention_heads,
            multi_query_group_num=multi_query_group_num,
            attention_dim=attention_dim,
            interleaved_qkv=interleaved_qkv,
        )

        complete_state_dict[f"model.language_model.layers.{layer_i}.self_attn.q_proj.weight"] = q.clone()
        complete_state_dict[f"model.language_model.layers.{layer_i}.self_attn.k_proj.weight"] = k.clone()
        complete_state_dict[f"model.language_model.layers.{layer_i}.self_attn.v_proj.weight"] = v.clone()

        if f"decoder.layers.{layer_i}.self_attention.linear_qkv.bias" in full_weights:
            q_bias, k_bias, v_bias = merge_qkv(
                sd_list=full_weights[f"decoder.layers.{layer_i}.self_attention.linear_qkv.bias"],
                original_tp=origin_tp,
                num_attention_heads=num_attention_heads,
                multi_query_group_num=multi_query_group_num,
                attention_dim=attention_dim,
                interleaved_qkv=interleaved_qkv,
            )
            complete_state_dict[f"model.language_model.layers.{layer_i}.self_attn.q_proj.bias"] = q_bias.clone()
            complete_state_dict[f"model.language_model.layers.{layer_i}.self_attn.k_proj.bias"] = k_bias.clone()
            complete_state_dict[f"model.language_model.layers.{layer_i}.self_attn.v_proj.bias"] = v_bias.clone()

        o_proj = torch.cat(full_weights[f"decoder.layers.{layer_i}.self_attention.linear_proj.weight"], dim=1)
        complete_state_dict[f"model.language_model.layers.{layer_i}.self_attn.o_proj.weight"] = o_proj.clone()

        # MLP - Use gate_up_proj
        gate_up_proj = torch.cat(full_weights[f"decoder.layers.{layer_i}.mlp.linear_fc1.weight"], dim=0)
        complete_state_dict[f"model.language_model.layers.{layer_i}.mlp.gate_up_proj.weight"] = gate_up_proj.clone()
        complete_state_dict[f"model.language_model.layers.{layer_i}.mlp.down_proj.weight"] = torch.cat(
            full_weights[f"decoder.layers.{layer_i}.mlp.linear_fc2.weight"], dim=1
        )
        layer_i += 1

    # Embedd Model, LM Head, and Norm
    embed_tokens = torch.cat(full_weights["embedding.word_embeddings.weight"], dim=0)
    complete_state_dict["model.language_model.embed_tokens.weight"] = embed_tokens.clone()

    lm_head = torch.cat(full_weights["output_layer.weight"], dim=0)
    complete_state_dict["lm_head.weight"] = lm_head.clone()
    complete_state_dict["model.language_model.norm.weight"] = full_weights["decoder.final_layernorm.weight"].clone()

    # VLM
    for layer_i in range(vision_num_layers):
        complete_state_dict[f"model.visual.blocks.{layer_i}.norm1.weight"] = full_weights[
            f"vision_model.transformer.layers.{layer_i}.self_attention.linear_qkv.layer_norm_weight"
        ]
        complete_state_dict[f"model.visual.blocks.{layer_i}.norm2.weight"] = full_weights[
            f"vision_model.transformer.layers.{layer_i}.mlp.linear_fc1.layer_norm_weight"
        ]

        q, k, v = merge_qkv_vit(
            sd_list=full_weights[f"vision_model.transformer.layers.{layer_i}.self_attention.linear_qkv.weight"],
            original_tp=origin_tp,
            num_attention_heads=vit_n_head,
            multi_query_group_num=vit_n_head,
            attention_dim=attention_dim,
        )
        complete_state_dict[f"model.visual.blocks.{layer_i}.attn.qkv.weight"] = torch.cat((q, k, v), dim=0)

        proj_weight = torch.cat(
            full_weights[f"vision_model.transformer.layers.{layer_i}.self_attention.linear_proj.weight"], dim=1
        )
        complete_state_dict[f"model.visual.blocks.{layer_i}.attn.proj.weight"] = proj_weight.clone()

        gate_proj_weight, up_proj_weight = merge_glu_vit(
            full_weights[f"vision_model.transformer.layers.{layer_i}.mlp.linear_fc1.weight"]
        )

        complete_state_dict[f"model.visual.blocks.{layer_i}.mlp.gate_proj.weight"] = gate_proj_weight.clone()
        complete_state_dict[f"model.visual.blocks.{layer_i}.mlp.up_proj.weight"] = up_proj_weight.clone()

        down_proj_weight = torch.cat(
            full_weights[f"vision_model.transformer.layers.{layer_i}.mlp.linear_fc2.weight"], dim=1
        )
        complete_state_dict[f"model.visual.blocks.{layer_i}.mlp.down_proj.weight"] = down_proj_weight.clone()

    complete_state_dict["model.visual.downsample.weight"] = (
        full_weights["vision_model.downsample.weight"].clone().contiguous()
    )
    complete_state_dict["model.visual.downsample.bias"] = (
        full_weights["vision_model.downsample.bias"].clone().contiguous()
    )

    # Merger
    gate_proj, up_proj = merge_glu_vit(full_weights["vision_projection.encoder.linear_fc1.weight"])

    down_proj = torch.cat(full_weights["vision_projection.encoder.linear_fc2.weight"], dim=1)
    proj = torch.cat(full_weights["vision_projection.linear_fc_extra.weight"], dim=0)

    complete_state_dict["model.visual.merger.gate_proj.weight"] = gate_proj.clone().contiguous()
    complete_state_dict["model.visual.merger.up_proj.weight"] = up_proj.clone().contiguous()
    complete_state_dict["model.visual.merger.down_proj.weight"] = down_proj.clone().contiguous()
    complete_state_dict["model.visual.merger.proj.weight"] = proj.clone().contiguous()

    if "vision_projection.layer_norm.weight" in full_weights:
        complete_state_dict["model.visual.merger.post_projection_norm.weight"] = full_weights[
            "vision_projection.layer_norm.weight"
        ]
    if "vision_projection.layer_norm.bias" in full_weights:
        complete_state_dict["model.visual.merger.post_projection_norm.bias"] = full_weights[
            "vision_projection.layer_norm.bias"
        ]

    complete_state_dict["model.visual.embeddings.position_embedding.weight"] = (
        full_weights["vision_model.position_embeddings.weight"].clone().contiguous()
    )
    complete_state_dict["model.visual.patch_embed.proj.weight"] = (
        full_weights["vision_model.conv3d.weight"].clone().contiguous()
    )
    complete_state_dict["model.visual.patch_embed.proj.bias"] = (
        full_weights["vision_model.conv3d.bias"].clone().contiguous()
    )

    # Check for additional vision model norm layers mentioned in the expected output
    if "vision_model.post_conv_layernorm.weight" in full_weights:
        complete_state_dict["model.visual.post_conv_layernorm.weight"] = (
            full_weights["vision_model.post_conv_layernorm.weight"].clone().contiguous()
        )

    if "vision_model.post_layernorm.weight" in full_weights:
        complete_state_dict["model.visual.post_layernorm.weight"] = (
            full_weights["vision_model.post_layernorm.weight"].clone().contiguous()
        )

    print(f"Total keys in state dict: {len(complete_state_dict)}")

    save_sharded_model(
        complete_state_dict,
        output_path=output_path,
        max_shard_size_gb=5,
        num_layers=num_layers,
        vision_num_layers=vision_num_layers,
    )

    hf_config = {
        "architectures": ["Glm4vForConditionalGeneration"],
        "model_type": "glm4v",
        "image_start_token_id": model_config.get("image_start_token_id", 151339),
        "image_end_token_id": model_config.get("image_end_token_id", 151340),
        "video_start_token_id": model_config.get("video_start_token_id", 151341),
        "video_end_token_id": model_config.get("video_end_token_id", 151342),
        "transformers_version": "4.57.1",
    }
    txt_config = {
        "model_type": "glm4v_text",
        "attention_bias": model_config.get("add_qkv_bias", True),
        "attention_dropout": 0.0,
        "pad_token_id": model_config.get("pad_token_id", 151329),
        "eos_token_id": model_config.get("eos_token_id", [151329, 151336, 151338]),
        "image_token_id": model_config.get("image_token_id", 151363),
        "video_token_id": model_config.get("video_token_id", 151364),
        "hidden_act": text_config.get("hidden_act", "silu"),
        "hidden_size": text_config.get("hidden_size", 4096),
        "initializer_range": 0.02,
        "intermediate_size": text_config.get("intermediate_size", 13696),
        "max_position_embeddings": text_config.get("seq_length", 131072),
        "num_attention_heads": text_config.get("num_attention_heads", 32),
        "num_hidden_layers": text_config.get("num_layers", 40),
        "num_key_value_heads": text_config.get("num_key_value_heads", 2),
        "rms_norm_eps": text_config.get("layernorm_epsilon", 1e-05),
        "dtype": text_config.get("torch_dtype", "bfloat16"),
        "use_cache": text_config.get("use_cache", True),
        "vocab_size": text_config.get("vocab_size", 151552),
        "tie_word_embeddings": False,
        "rope_parameters": {
            "rope_type": "default",
            "rope_theta": 10000.0,
            "mrope_section": [8, 12, 12],
            "partial_rotary_factor": 0.5,
        },
    }
    hf_config["text_config"] = txt_config

    if "vision_config" in model_config:
        vision_config = {
            "model_type": "glm4v_vision",
            "hidden_size": model_config["vision_config"].get("hidden_size", 1536),
            "depth": model_config["vision_config"].get("num_layers", 24),
            "num_heads": model_config["vision_config"].get("num_attention_heads", 12),
            "attention_bias": model_config["vision_config"].get("attention_bias", False),
            "intermediate_size": model_config.get("ffn_hidden_size", 13696),
            "hidden_act": model_config["vision_config"].get("hidden_act", "silu"),
            "hidden_dropout_prob": model_config["vision_config"].get("hidden_dropout_prob", 0.0),
            "initializer_range": 0.02,
            "image_size": model_config["vision_config"].get("image_size", 336),
            "patch_size": model_config["vision_config"].get("patch_size", 14),
            "out_hidden_size": model_config.get("hidden_size", 4096),
            "rms_norm_eps": model_config["vision_config"].get("layernorm_epsilon", 1e-05),
            "spatial_merge_size": model_config["vision_config"].get("downsample_ratio", 2),
            "temporal_patch_size": model_config["vision_config"].get("t_patch", 2),
        }
        hf_config["vision_config"] = vision_config

    config_path = os.path.join(output_path, "config.json")
    with open(config_path, "w") as f:
        json.dump(hf_config, f, indent=2)

    print(f"Conversion complete! Model saved to {output_path}")