def load_clipvision_from_sd(sd, prefix="", convert_keys=False):
    if convert_keys:
        sd = convert_to_transformers(sd, prefix)
    if "vision_model.encoder.layers.47.layer_norm1.weight" in sd:
        json_config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "clip_vision_config_g.json")
    elif "vision_model.encoder.layers.30.layer_norm1.weight" in sd:
        json_config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "clip_vision_config_h.json")
    elif "vision_model.encoder.layers.22.layer_norm1.weight" in sd:
        embed_shape = sd["vision_model.embeddings.position_embedding.weight"].shape[0]
        if sd["vision_model.encoder.layers.0.layer_norm1.weight"].shape[0] == 1152:
            patch_embedding_shape = sd["vision_model.embeddings.patch_embedding.weight"].shape
            if len(patch_embedding_shape) == 2:
                json_config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "clip_vision_siglip2_base_naflex.json")
            else:
                if embed_shape == 729:
                    json_config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "clip_vision_siglip_384.json")
                elif embed_shape == 1024:
                    json_config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "clip_vision_siglip_512.json")
        elif embed_shape == 577:
            if "multi_modal_projector.linear_1.bias" in sd:
                json_config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "clip_vision_config_vitl_336_llava.json")
            else:
                json_config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "clip_vision_config_vitl_336.json")
        else:
            json_config = os.path.join(os.path.dirname(os.path.realpath(__file__)), "clip_vision_config_vitl.json")

    # Dinov2
    elif 'encoder.layer.39.layer_scale2.lambda1' in sd:
        json_config = os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__)), "image_encoders"), "dino2_giant.json")
    elif 'encoder.layer.23.layer_scale2.lambda1' in sd:
        json_config = os.path.join(os.path.join(os.path.dirname(os.path.realpath(__file__)), "image_encoders"), "dino2_large.json")
    else:
        return None

    clip = ClipVisionModel(json_config)
    m, u = clip.load_sd(sd)
    if len(m) > 0:
        logging.warning("missing clip vision: {}".format(m))
    u = set(u)
    keys = list(sd.keys())
    for k in keys:
        if k not in u:
            sd.pop(k)
    return clip