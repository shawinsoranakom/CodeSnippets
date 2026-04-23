def rename_keys(state_dict):
    new_state_dict = OrderedDict()
    for key, value in state_dict.items():
        if key.startswith("module.encoder"):
            key = key.replace("module.encoder", "glpn.encoder")
        if key.startswith("module.decoder"):
            key = key.replace("module.decoder", "decoder.stages")
        if "patch_embed" in key:
            # replace for example patch_embed1 by patch_embeddings.0
            idx = key[key.find("patch_embed") + len("patch_embed")]
            key = key.replace(f"patch_embed{idx}", f"patch_embeddings.{int(idx) - 1}")
        if "norm" in key:
            key = key.replace("norm", "layer_norm")
        if "glpn.encoder.layer_norm" in key:
            # replace for example layer_norm1 by layer_norm.0
            idx = key[key.find("glpn.encoder.layer_norm") + len("glpn.encoder.layer_norm")]
            key = key.replace(f"layer_norm{idx}", f"layer_norm.{int(idx) - 1}")
        if "layer_norm1" in key:
            key = key.replace("layer_norm1", "layer_norm_1")
        if "layer_norm2" in key:
            key = key.replace("layer_norm2", "layer_norm_2")
        if "block" in key:
            # replace for example block1 by block.0
            idx = key[key.find("block") + len("block")]
            key = key.replace(f"block{idx}", f"block.{int(idx) - 1}")
        if "attn.q" in key:
            key = key.replace("attn.q", "attention.self.query")
        if "attn.proj" in key:
            key = key.replace("attn.proj", "attention.output.dense")
        if "attn" in key:
            key = key.replace("attn", "attention.self")
        if "fc1" in key:
            key = key.replace("fc1", "dense1")
        if "fc2" in key:
            key = key.replace("fc2", "dense2")
        if "linear_pred" in key:
            key = key.replace("linear_pred", "classifier")
        if "linear_fuse" in key:
            key = key.replace("linear_fuse.conv", "linear_fuse")
            key = key.replace("linear_fuse.bn", "batch_norm")
        if "linear_c" in key:
            # replace for example linear_c4 by linear_c.3
            idx = key[key.find("linear_c") + len("linear_c")]
            key = key.replace(f"linear_c{idx}", f"linear_c.{int(idx) - 1}")
        if "bot_conv" in key:
            key = key.replace("bot_conv", "0.convolution")
        if "skip_conv1" in key:
            key = key.replace("skip_conv1", "1.convolution")
        if "skip_conv2" in key:
            key = key.replace("skip_conv2", "2.convolution")
        if "fusion1" in key:
            key = key.replace("fusion1", "1.fusion")
        if "fusion2" in key:
            key = key.replace("fusion2", "2.fusion")
        if "fusion3" in key:
            key = key.replace("fusion3", "3.fusion")
        if "fusion" in key and "conv" in key:
            key = key.replace("conv", "convolutional_layer")
        if key.startswith("module.last_layer_depth"):
            key = key.replace("module.last_layer_depth", "head.head")
        new_state_dict[key] = value

    return new_state_dict