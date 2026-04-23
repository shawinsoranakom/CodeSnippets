def get_dpt_config(model_name):
    if "small" in model_name:
        out_indices = [3, 6, 9, 12] if "v2" in model_name else [9, 10, 11, 12]
        backbone_config = Dinov2Config.from_pretrained(
            "facebook/dinov2-small", out_indices=out_indices, apply_layernorm=True, reshape_hidden_states=False
        )
        fusion_hidden_size = 64
        neck_hidden_sizes = [48, 96, 192, 384]
    elif "base" in model_name:
        out_indices = [3, 6, 9, 12] if "v2" in model_name else [9, 10, 11, 12]
        backbone_config = Dinov2Config.from_pretrained(
            "facebook/dinov2-base", out_indices=out_indices, apply_layernorm=True, reshape_hidden_states=False
        )
        fusion_hidden_size = 128
        neck_hidden_sizes = [96, 192, 384, 768]
    elif "large" in model_name:
        out_indices = [5, 12, 18, 24] if "v2" in model_name else [21, 22, 23, 24]
        backbone_config = Dinov2Config.from_pretrained(
            "facebook/dinov2-large", out_indices=out_indices, apply_layernorm=True, reshape_hidden_states=False
        )
        fusion_hidden_size = 256
        neck_hidden_sizes = [256, 512, 1024, 1024]
    else:
        raise NotImplementedError(f"Model not supported: {model_name}")

    if "metric" in model_name:
        depth_estimation_type = "metric"
        max_depth = 20 if "indoor" in model_name else 80
    else:
        depth_estimation_type = "relative"
        max_depth = None

    config = DepthAnythingConfig(
        reassemble_hidden_size=backbone_config.hidden_size,
        patch_size=backbone_config.patch_size,
        backbone_config=backbone_config,
        fusion_hidden_size=fusion_hidden_size,
        neck_hidden_sizes=neck_hidden_sizes,
        depth_estimation_type=depth_estimation_type,
        max_depth=max_depth,
    )

    return config