def rename_keys(s_dict):
    # 1. in HF T5, we have block.{x}.layer.{y}. which corresponds to layer.{x} in
    # the original model
    keys = list(s_dict.keys())
    for key in keys:
        layer_to_block_of_layer = r".*/layers_(\d+)"
        new_key = key
        if re.match(layer_to_block_of_layer, key):
            new_key = re.sub(r"layers_(\d+)", r"block/\1/layer", new_key)

        layer_to_block_of_layer = r"(encoder|decoder)\/"

        if re.match(layer_to_block_of_layer, key):
            groups = re.match(layer_to_block_of_layer, new_key).groups()
            if groups[0] == "encoder":
                new_key = re.sub(r"/mlp/", r"/1/mlp/", new_key)
                new_key = re.sub(r"/pre_mlp_layer_norm/", r"/1/layer_norm/", new_key)

            elif groups[0] == "decoder":
                new_key = re.sub(r"/mlp/", r"/2/mlp/", new_key)
                new_key = re.sub(r"/pre_mlp_layer_norm/", r"/2/layer_norm/", new_key)

        # 2. Convert other classic mappings
        for old_key, temp_key in MOE_LAYER_NAME_MAPPING.items():
            if old_key in new_key:
                new_key = new_key.replace(old_key, temp_key)

        print(f"{key} -> {new_key}")
        s_dict[new_key] = s_dict.pop(key)

    if "encoder/block/0/layer/0/SelfAttention/relative_attention_bias/weight" in s_dict:
        s_dict["encoder/block/0/layer/0/SelfAttention/relative_attention_bias/weight"] = s_dict[
            "encoder/block/0/layer/0/SelfAttention/relative_attention_bias/weight"
        ].T
    if "decoder/block/0/layer/0/SelfAttention/relative_attention_bias/weight" in s_dict:
        s_dict["decoder/block/0/layer/0/SelfAttention/relative_attention_bias/weight"] = s_dict[
            "decoder/block/0/layer/0/SelfAttention/relative_attention_bias/weight"
        ].T

    # 3. Take extra care of the EXPERTS layer
    for key in list(s_dict.keys()):
        if "expert" in key:
            num_experts = s_dict[key].shape[0]
            expert_weihts = s_dict[key]
            for idx in range(num_experts):
                s_dict[key.replace("expert/", f"experts/expert_{idx}/")] = expert_weihts[idx]
                print(f"{key} -> {key.replace('expert/', f'experts/expert_{idx}/')}")

            s_dict.pop(key)

    return s_dict