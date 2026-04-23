def prepare_config(size_config_url, size):
    config_dict = httpx.get(size_config_url).json()

    backbone_config = {}
    for stage_ix in range(1, 5):
        stage_config = config_dict[f"stage{stage_ix}"]

        merged_dict = {}

        # Iterate through the list of dictionaries
        for layer in stage_config:
            for key, value in layer.items():
                if key != "name":
                    # Check if the key is already in the merged_dict
                    if key in merged_dict:
                        merged_dict[key].append(value)
                    else:
                        # If the key is not in merged_dict, create a new list with the value
                        merged_dict[key] = [value]
        backbone_config[f"stage{stage_ix}"] = merged_dict

    neck_in_channels = []
    neck_out_channels = []
    neck_kernel_size = []
    neck_stride = []
    neck_dilation = []
    neck_groups = []

    for i in range(1, 5):
        layer_key = f"reduce_layer{i}"
        layer_dict = config_dict["neck"].get(layer_key)

        if layer_dict:
            # Append values to the corresponding lists
            neck_in_channels.append(layer_dict["in_channels"])
            neck_out_channels.append(layer_dict["out_channels"])
            neck_kernel_size.append(layer_dict["kernel_size"])
            neck_stride.append(layer_dict["stride"])
            neck_dilation.append(layer_dict["dilation"])
            neck_groups.append(layer_dict["groups"])

    textnet_config = TextNetConfig(
        stem_kernel_size=config_dict["first_conv"]["kernel_size"],
        stem_stride=config_dict["first_conv"]["stride"],
        stem_num_channels=config_dict["first_conv"]["in_channels"],
        stem_out_channels=config_dict["first_conv"]["out_channels"],
        stem_act_func=config_dict["first_conv"]["act_func"],
        conv_layer_kernel_sizes=[
            backbone_config["stage1"]["kernel_size"],
            backbone_config["stage2"]["kernel_size"],
            backbone_config["stage3"]["kernel_size"],
            backbone_config["stage4"]["kernel_size"],
        ],
        conv_layer_strides=[
            backbone_config["stage1"]["stride"],
            backbone_config["stage2"]["stride"],
            backbone_config["stage3"]["stride"],
            backbone_config["stage4"]["stride"],
        ],
        hidden_sizes=[
            config_dict["first_conv"]["out_channels"],
            backbone_config["stage1"]["out_channels"][-1],
            backbone_config["stage2"]["out_channels"][-1],
            backbone_config["stage3"]["out_channels"][-1],
            backbone_config["stage4"]["out_channels"][-1],
        ],
        out_features=["stage1", "stage2", "stage3", "stage4"],
        out_indices=[1, 2, 3, 4],
    )

    return textnet_config