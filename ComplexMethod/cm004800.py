def get_dpt_config(model_name):
    if "tiny" in model_name:
        embed_dim = 96
        depths = (2, 2, 6, 2)
        num_heads = (3, 6, 12, 24)
        window_size = 16
        # note: for Swinv2-tiny authors used the window_size = 16 variant
        # as seen here: https://github.com/isl-org/MiDaS/blob/bdc4ed64c095e026dc0a2f17cabb14d58263decb/midas/backbones/swin2.py#L26
        pretrained_window_sizes = (0, 0, 0, 0)
    elif "base" in model_name:
        embed_dim = 128
        depths = (2, 2, 18, 2)
        num_heads = (4, 8, 16, 32)
        window_size = 24
        pretrained_window_sizes = (12, 12, 12, 6)
    elif "large" in model_name:
        embed_dim = 192
        depths = (2, 2, 18, 2)
        num_heads = (6, 12, 24, 48)
        window_size = 24
        pretrained_window_sizes = (12, 12, 12, 6)

    if "384" in model_name:
        image_size = 384
    elif "256" in model_name:
        image_size = 256
    else:
        raise ValueError("Model not supported, to do")

    backbone_config = Swinv2Config(
        image_size=image_size,
        embed_dim=embed_dim,
        depths=depths,
        window_size=window_size,
        pretrained_window_sizes=pretrained_window_sizes,
        num_heads=num_heads,
        out_features=["stage1", "stage2", "stage3", "stage4"],
    )

    if model_name == "dpt-swinv2-tiny-256":
        neck_hidden_sizes = [96, 192, 384, 768]
    elif model_name == "dpt-swinv2-base-384":
        neck_hidden_sizes = [128, 256, 512, 1024]
    elif model_name == "dpt-swinv2-large-384":
        neck_hidden_sizes = [192, 384, 768, 1536]

    config = DPTConfig(backbone_config=backbone_config, neck_hidden_sizes=neck_hidden_sizes)

    return config, image_size