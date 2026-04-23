def rename_key(name, base_model=False):
    for i in range(1, 6):
        if f"layer_{i}." in name:
            name = name.replace(f"layer_{i}.", f"encoder.layer.{i - 1}.")

    if "conv_1." in name:
        name = name.replace("conv_1.", "conv_stem.")
    if ".block." in name:
        name = name.replace(".block.", ".")

    if "exp_1x1" in name:
        name = name.replace("exp_1x1", "expand_1x1")
    if "red_1x1" in name:
        name = name.replace("red_1x1", "reduce_1x1")
    if ".local_rep.conv_3x3." in name:
        name = name.replace(".local_rep.conv_3x3.", ".conv_kxk.")
    if ".local_rep.conv_1x1." in name:
        name = name.replace(".local_rep.conv_1x1.", ".conv_1x1.")
    if ".norm." in name:
        name = name.replace(".norm.", ".normalization.")
    if ".conv." in name:
        name = name.replace(".conv.", ".convolution.")
    if ".conv_proj." in name:
        name = name.replace(".conv_proj.", ".conv_projection.")

    for i in range(0, 2):
        for j in range(0, 4):
            if f".{i}.{j}." in name:
                name = name.replace(f".{i}.{j}.", f".{i}.layer.{j}.")

    for i in range(2, 6):
        for j in range(0, 4):
            if f".{i}.{j}." in name:
                name = name.replace(f".{i}.{j}.", f".{i}.")
                if "expand_1x1" in name:
                    name = name.replace("expand_1x1", "downsampling_layer.expand_1x1")
                if "conv_3x3" in name:
                    name = name.replace("conv_3x3", "downsampling_layer.conv_3x3")
                if "reduce_1x1" in name:
                    name = name.replace("reduce_1x1", "downsampling_layer.reduce_1x1")

    for i in range(2, 5):
        if f".global_rep.{i}.weight" in name:
            name = name.replace(f".global_rep.{i}.weight", ".layernorm.weight")
        if f".global_rep.{i}.bias" in name:
            name = name.replace(f".global_rep.{i}.bias", ".layernorm.bias")

    if ".global_rep." in name:
        name = name.replace(".global_rep.", ".transformer.")
    if ".pre_norm_mha.0." in name:
        name = name.replace(".pre_norm_mha.0.", ".layernorm_before.")
    if ".pre_norm_mha.1.out_proj." in name:
        name = name.replace(".pre_norm_mha.1.out_proj.", ".attention.output.dense.")
    if ".pre_norm_ffn.0." in name:
        name = name.replace(".pre_norm_ffn.0.", ".layernorm_after.")
    if ".pre_norm_ffn.1." in name:
        name = name.replace(".pre_norm_ffn.1.", ".intermediate.dense.")
    if ".pre_norm_ffn.4." in name:
        name = name.replace(".pre_norm_ffn.4.", ".output.dense.")
    if ".transformer." in name:
        name = name.replace(".transformer.", ".transformer.layer.")

    if ".aspp_layer." in name:
        name = name.replace(".aspp_layer.", ".")
    if ".aspp_pool." in name:
        name = name.replace(".aspp_pool.", ".")
    if "seg_head." in name:
        name = name.replace("seg_head.", "segmentation_head.")
    if "segmentation_head.classifier.classifier." in name:
        name = name.replace("segmentation_head.classifier.classifier.", "segmentation_head.classifier.")

    if "classifier.fc." in name:
        name = name.replace("classifier.fc.", "classifier.")
    elif (not base_model) and ("segmentation_head." not in name):
        name = "mobilevit." + name

    return name