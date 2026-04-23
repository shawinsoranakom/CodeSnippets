def load_checkpoint(checkpoint_path):
    """Checkpoint path should end in model.pt"""
    sd = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    if "model" in sd:
        sd = torch.load(checkpoint_path, map_location="cpu", weights_only=True)["model"]

    # pop unnecessary weights
    keys_to_delete = [
        "decoder.version",
        "decoder.output_projection.weight",
    ]
    for key in keys_to_delete:
        if key in sd:
            sd.pop(key)

    keys_to_rename = {
        "decoder.project_in_dim.weight": "decoder.project_in.weight",
        "decoder.project_out_dim.weight": "decoder.project_out.weight",
        "decoder.layer_norm.weight": "decoder.final_layer_norm.weight",
        "decoder.layer_norm.bias": "decoder.final_layer_norm.bias",
    }
    for old_key, new_key in keys_to_rename.items():
        if old_key in sd:
            sd[new_key] = sd.pop(old_key)

    keys = list(sd.keys())
    for key in keys:
        if ".qkv_proj." in key:
            value = sd[key]
            # We split QKV in separate Q,K,V

            q_name = key.replace(".qkv_proj.", ".q_proj.")
            k_name = key.replace(".qkv_proj.", ".k_proj.")
            v_name = key.replace(".qkv_proj.", ".v_proj.")

            depth = value.shape[0]
            assert depth % 3 == 0
            # `SequeuceParallelTransformerBlock` has QKV weight is separated in K,V,Q despite the naming:
            # https://cs.github.com/facebookresearch/metaseq/blob/51871bd73cd04c038f239ea2a26db1d7f6b37927/metaseq/modules/sequence_parallel_transformer_layer.py#L97
            k, v, q = torch.split(value, depth // 3, dim=0)

            sd[q_name] = q
            sd[k_name] = k
            sd[v_name] = v
            del sd[key]

    return sd