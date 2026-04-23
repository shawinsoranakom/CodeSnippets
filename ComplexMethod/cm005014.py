def rename_key(name):
    if "downsample_layers.0.0" in name:
        name = name.replace("downsample_layers.0.0", "embeddings.patch_embeddings")
    if "downsample_layers.0.1" in name:
        name = name.replace("downsample_layers.0.1", "embeddings.norm")  # we rename to layernorm later on
    if "downsample_layers.1.0" in name:
        name = name.replace("downsample_layers.1.0", "stages.1.downsampling_layer.0")
    if "downsample_layers.1.1" in name:
        name = name.replace("downsample_layers.1.1", "stages.1.downsampling_layer.1")
    if "downsample_layers.2.0" in name:
        name = name.replace("downsample_layers.2.0", "stages.2.downsampling_layer.0")
    if "downsample_layers.2.1" in name:
        name = name.replace("downsample_layers.2.1", "stages.2.downsampling_layer.1")
    if "downsample_layers.3.0" in name:
        name = name.replace("downsample_layers.3.0", "stages.3.downsampling_layer.0")
    if "downsample_layers.3.1" in name:
        name = name.replace("downsample_layers.3.1", "stages.3.downsampling_layer.1")
    if "stages" in name and "downsampling_layer" not in name:
        # stages.0.0. for instance should be renamed to stages.0.layers.0.
        name = name[: len("stages.0")] + ".layers" + name[len("stages.0") :]
    if "gamma" in name:
        name = name.replace("gamma", "weight")
    if "beta" in name:
        name = name.replace("beta", "bias")
    if "stages" in name:
        name = name.replace("stages", "encoder.stages")
    if "norm" in name:
        name = name.replace("norm", "layernorm")
    if "head" in name:
        name = name.replace("head", "classifier")

    return name