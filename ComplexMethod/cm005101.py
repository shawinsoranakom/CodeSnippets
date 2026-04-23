def get_zoedepth_config(model_name):
    image_size = 384
    backbone_config = BeitConfig(
        image_size=image_size,
        num_hidden_layers=24,
        hidden_size=1024,
        intermediate_size=4096,
        num_attention_heads=16,
        use_relative_position_bias=True,
        reshape_hidden_states=False,
        out_features=["stage6", "stage12", "stage18", "stage24"],  # beit-large-512 uses [5, 11, 17, 23],
    )

    neck_hidden_sizes = [256, 512, 1024, 1024]
    bin_centers_type = "softplus" if model_name in ["ZoeD_N", "ZoeD_NK"] else "normed"
    if model_name == "ZoeD_NK":
        bin_configurations = [
            {"name": "nyu", "n_bins": 64, "min_depth": 1e-3, "max_depth": 10.0},
            {"name": "kitti", "n_bins": 64, "min_depth": 1e-3, "max_depth": 80.0},
        ]
    elif model_name in ["ZoeD_N", "ZoeD_K"]:
        bin_configurations = [
            {"name": "nyu", "n_bins": 64, "min_depth": 1e-3, "max_depth": 10.0},
        ]
    config = ZoeDepthConfig(
        backbone_config=backbone_config,
        neck_hidden_sizes=neck_hidden_sizes,
        bin_centers_type=bin_centers_type,
        bin_configurations=bin_configurations,
        num_patch_transformer_layers=4 if model_name == "ZoeD_NK" else None,
        patch_transformer_hidden_size=128 if model_name == "ZoeD_NK" else None,
        patch_transformer_intermediate_size=1024 if model_name == "ZoeD_NK" else None,
        patch_transformer_num_attention_heads=4 if model_name == "ZoeD_NK" else None,
    )

    return config, image_size