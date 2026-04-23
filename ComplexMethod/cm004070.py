def rename_key(name):
    if "patch_embed.proj" in name:
        name = name.replace("patch_embed.proj", "embeddings.patch_embeddings.projection")
    if "patch_embed.norm" in name:
        name = name.replace("patch_embed.norm", "embeddings.norm")
    if "layers" in name:
        name = "encoder." + name
    if "encoder.layers" in name:
        name = name.replace("encoder.layers", "encoder.stages")
    if "downsample.proj" in name:
        name = name.replace("downsample.proj", "downsample.projection")
    if "blocks" in name:
        name = name.replace("blocks", "layers")
    if "modulation.f.weight" in name or "modulation.f.bias" in name:
        name = name.replace("modulation.f", "modulation.projection_in")
    if "modulation.h.weight" in name or "modulation.h.bias" in name:
        name = name.replace("modulation.h", "modulation.projection_context")
    if "modulation.proj.weight" in name or "modulation.proj.bias" in name:
        name = name.replace("modulation.proj", "modulation.projection_out")

    if name == "norm.weight":
        name = "layernorm.weight"
    if name == "norm.bias":
        name = "layernorm.bias"

    if "head" in name:
        name = name.replace("head", "classifier")
    else:
        name = "focalnet." + name

    return name