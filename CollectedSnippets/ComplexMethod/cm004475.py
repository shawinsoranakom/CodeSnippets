def create_rename_keys(state_dict, base_model=False):
    if base_model:
        model_prefix = ""
    else:
        model_prefix = "mobilevitv2."

    rename_keys = []
    for k in state_dict:
        if k[:8] == "encoder.":
            k_new = k[8:]
        else:
            k_new = k

        if ".block." in k:
            k_new = k_new.replace(".block.", ".")
        if ".conv." in k:
            k_new = k_new.replace(".conv.", ".convolution.")
        if ".norm." in k:
            k_new = k_new.replace(".norm.", ".normalization.")

        if "conv_1." in k:
            k_new = k_new.replace("conv_1.", f"{model_prefix}conv_stem.")
        for i in [1, 2]:
            if f"layer_{i}." in k:
                k_new = k_new.replace(f"layer_{i}.", f"{model_prefix}encoder.layer.{i - 1}.layer.")
        if ".exp_1x1." in k:
            k_new = k_new.replace(".exp_1x1.", ".expand_1x1.")
        if ".red_1x1." in k:
            k_new = k_new.replace(".red_1x1.", ".reduce_1x1.")

        for i in [3, 4, 5]:
            if f"layer_{i}.0." in k:
                k_new = k_new.replace(f"layer_{i}.0.", f"{model_prefix}encoder.layer.{i - 1}.downsampling_layer.")
            if f"layer_{i}.1.local_rep.0." in k:
                k_new = k_new.replace(f"layer_{i}.1.local_rep.0.", f"{model_prefix}encoder.layer.{i - 1}.conv_kxk.")
            if f"layer_{i}.1.local_rep.1." in k:
                k_new = k_new.replace(f"layer_{i}.1.local_rep.1.", f"{model_prefix}encoder.layer.{i - 1}.conv_1x1.")

        for i in [3, 4, 5]:
            if i == 3:
                j_in = [0, 1]
            elif i == 4:
                j_in = [0, 1, 2, 3]
            elif i == 5:
                j_in = [0, 1, 2]

            for j in j_in:
                if f"layer_{i}.1.global_rep.{j}." in k:
                    k_new = k_new.replace(
                        f"layer_{i}.1.global_rep.{j}.", f"{model_prefix}encoder.layer.{i - 1}.transformer.layer.{j}."
                    )
            if f"layer_{i}.1.global_rep.{j + 1}." in k:
                k_new = k_new.replace(
                    f"layer_{i}.1.global_rep.{j + 1}.", f"{model_prefix}encoder.layer.{i - 1}.layernorm."
                )

            if f"layer_{i}.1.conv_proj." in k:
                k_new = k_new.replace(
                    f"layer_{i}.1.conv_proj.", f"{model_prefix}encoder.layer.{i - 1}.conv_projection."
                )

        if "pre_norm_attn.0." in k:
            k_new = k_new.replace("pre_norm_attn.0.", "layernorm_before.")
        if "pre_norm_attn.1." in k:
            k_new = k_new.replace("pre_norm_attn.1.", "attention.")
        if "pre_norm_ffn.0." in k:
            k_new = k_new.replace("pre_norm_ffn.0.", "layernorm_after.")
        if "pre_norm_ffn.1." in k:
            k_new = k_new.replace("pre_norm_ffn.1.", "ffn.conv1.")
        if "pre_norm_ffn.3." in k:
            k_new = k_new.replace("pre_norm_ffn.3.", "ffn.conv2.")

        if "classifier.1." in k:
            k_new = k_new.replace("classifier.1.", "classifier.")

        if "seg_head." in k:
            k_new = k_new.replace("seg_head.", "segmentation_head.")
        if ".aspp_layer." in k:
            k_new = k_new.replace(".aspp_layer.", ".")
        if ".aspp_pool." in k:
            k_new = k_new.replace(".aspp_pool.", ".")

        rename_keys.append((k, k_new))
    return rename_keys