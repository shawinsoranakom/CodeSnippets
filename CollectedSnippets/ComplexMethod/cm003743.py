def preprocess_old_state(state_dict: dict, config: MMGroundingDinoConfig) -> dict:
    """
    Preprocesses old state dict to enable 1-1 mapping:
        - split qkv projections in Swin backbone
        - reorder reduction and norm parameters in Swin backbone
        - shift output norm indices in Swin backbone
        - shift output proj indices in neck
        - split q,k,v projections in text self and cross attentions in encoder and decoder
        - duplicate detection head parameters for decoder and encoder
    """
    new_state_dict = state_dict.copy()
    for k in state_dict:
        if k.startswith("backbone"):
            if "downsample.reduction" in k:
                new_state_dict[k] = correct_unfold_reduction_order(new_state_dict.pop(k))
            elif "downsample.norm" in k:
                new_state_dict[k] = correct_unfold_norm_order(new_state_dict.pop(k))
            elif "w_msa.qkv" in k:
                q_param, k_param, v_param = new_state_dict.pop(k).chunk(3)
                new_state_dict[k.replace("qkv", "query")] = q_param
                new_state_dict[k.replace("qkv", "key")] = k_param
                new_state_dict[k.replace("qkv", "value")] = v_param
            elif "backbone.norm" in k:
                match = re.match(r"backbone.norm(\d+).(weight|bias)", k)
                new_state_dict[f"backbone.norms.{int(match.group(1)) + 1}.{match.group(2)}"] = new_state_dict.pop(k)
        elif k.startswith("neck.extra_convs"):
            num_normal_convs = len(config.backbone_config.out_indices)
            if "gn" in k:
                match = re.match(r"neck.extra_convs.(\d+).gn.(weight|bias)", k)
                new_state_dict[f"neck.extra_convs.{num_normal_convs + int(match.group(1))}.gn.{match.group(2)}"] = (
                    new_state_dict.pop(k)
                )
            elif "conv" in k:
                match = re.match(r"neck.extra_convs.(\d+).conv.(weight|bias)", k)
                new_state_dict[f"neck.extra_convs.{num_normal_convs + int(match.group(1))}.conv.{match.group(2)}"] = (
                    new_state_dict.pop(k)
                )
        elif k.startswith("encoder"):
            if "self_attn.attn.in_proj" in k:
                q_param, k_param, v_param = new_state_dict.pop(k).chunk(3)
                new_state_dict[k.replace("in", "query")] = q_param
                new_state_dict[k.replace("in", "key")] = k_param
                new_state_dict[k.replace("in", "value")] = v_param
        elif k.startswith("decoder"):
            if "self_attn.attn.in_proj" in k or "cross_attn_text.attn.in_proj" in k:
                q_param, k_param, v_param = new_state_dict.pop(k).chunk(3)
                new_state_dict[k.replace("in", "query")] = q_param
                new_state_dict[k.replace("in", "key")] = k_param
                new_state_dict[k.replace("in", "value")] = v_param
        elif k.startswith("bbox_head"):
            num_decoder_layers = config.decoder_layers
            match = re.match(r"bbox_head.(cls|reg)_branches.(\d+).(.*)", k)
            cls_or_reg = match.group(1)
            layer_idx = int(match.group(2))
            suffix = match.group(3)
            if layer_idx < num_decoder_layers:
                new_key = f"decoder.bbox_head.{cls_or_reg}_branches.{layer_idx}.{suffix}"
                new_state_dict[new_key] = new_state_dict[k]  # copy
            else:
                new_key = f"encoder.bbox_head.{cls_or_reg}_branch.{suffix}"
                new_state_dict[new_key] = new_state_dict.pop(k)  # move

        # remove unused params
        if (
            k == "dn_query_generator.label_embedding.weight"
            or k == "language_model.language_backbone.body.model.embeddings.position_ids"
            or k == "image_seperate.weight"
            or k.startswith("lmm")
            or k.startswith("connector")
            or k.startswith("region_connector")
            or k.startswith("ref_point_head")
        ):
            new_state_dict.pop(k)

    return new_state_dict