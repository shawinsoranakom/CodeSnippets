def get_config(model_name):
    if "plus" in model_name:
        num_experts = 6
        if "small" in model_name:
            part_features = 96
            out_indices = [12]
        elif "base" in model_name:
            part_features = 192
            out_indices = [12]
        elif "large" in model_name:
            part_features = 256
            out_indices = [24]
        elif "huge" in model_name:
            part_features = 320
            out_indices = [32]
        else:
            raise ValueError(f"Model {model_name} not supported")
    else:
        num_experts = 1
        part_features = 0

    # size of the architecture
    if "small" in model_name:
        hidden_size = 384
        num_hidden_layers = 12
        num_attention_heads = 12
    elif "large" in model_name:
        hidden_size = 1024
        num_hidden_layers = 24
        num_attention_heads = 16
    elif "huge" in model_name:
        hidden_size = 1280
        num_hidden_layers = 32
        num_attention_heads = 16

    backbone_config = VitPoseBackboneConfig(
        out_indices=out_indices,
        hidden_size=hidden_size,
        num_hidden_layers=num_hidden_layers,
        num_attention_heads=num_attention_heads,
        num_experts=num_experts,
        part_features=part_features,
    )

    use_simple_decoder = "simple" in model_name

    edges = [
        [15, 13],
        [13, 11],
        [16, 14],
        [14, 12],
        [11, 12],
        [5, 11],
        [6, 12],
        [5, 6],
        [5, 7],
        [6, 8],
        [7, 9],
        [8, 10],
        [1, 2],
        [0, 1],
        [0, 2],
        [1, 3],
        [2, 4],
        [3, 5],
        [4, 6],
    ]
    id2label = {
        0: "Nose",
        1: "L_Eye",
        2: "R_Eye",
        3: "L_Ear",
        4: "R_Ear",
        5: "L_Shoulder",
        6: "R_Shoulder",
        7: "L_Elbow",
        8: "R_Elbow",
        9: "L_Wrist",
        10: "R_Wrist",
        11: "L_Hip",
        12: "R_Hip",
        13: "L_Knee",
        14: "R_Knee",
        15: "L_Ankle",
        16: "R_Ankle",
    }

    label2id = {v: k for k, v in id2label.items()}

    config = VitPoseConfig(
        backbone_config=backbone_config,
        num_labels=17,
        use_simple_decoder=use_simple_decoder,
        edges=edges,
        id2label=id2label,
        label2id=label2id,
    )

    return config