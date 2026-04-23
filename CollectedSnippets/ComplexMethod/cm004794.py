def rename_key(name):
    if (
        "pretrained.model" in name
        and "cls_token" not in name
        and "pos_embed" not in name
        and "patch_embed" not in name
    ):
        name = name.replace("pretrained.model", "dpt.encoder")
    if "pretrained.model" in name:
        name = name.replace("pretrained.model", "dpt.embeddings")
    if "patch_embed" in name:
        name = name.replace("patch_embed", "patch_embeddings")
    if "pos_embed" in name:
        name = name.replace("pos_embed", "position_embeddings")
    if "attn.proj" in name:
        name = name.replace("attn.proj", "attention.output.dense")
    if "proj" in name and "project" not in name:
        name = name.replace("proj", "projection")
    if "blocks" in name:
        name = name.replace("blocks", "layer")
    if "mlp.fc1" in name:
        name = name.replace("mlp.fc1", "intermediate.dense")
    if "mlp.fc2" in name:
        name = name.replace("mlp.fc2", "output.dense")
    if "norm1" in name:
        name = name.replace("norm1", "layernorm_before")
    if "norm2" in name:
        name = name.replace("norm2", "layernorm_after")
    if "scratch.output_conv" in name:
        name = name.replace("scratch.output_conv", "head")
    if "scratch" in name:
        name = name.replace("scratch", "neck")
    if "layer1_rn" in name:
        name = name.replace("layer1_rn", "convs.0")
    if "layer2_rn" in name:
        name = name.replace("layer2_rn", "convs.1")
    if "layer3_rn" in name:
        name = name.replace("layer3_rn", "convs.2")
    if "layer4_rn" in name:
        name = name.replace("layer4_rn", "convs.3")
    if "refinenet" in name:
        layer_idx = int(name[len("neck.refinenet") : len("neck.refinenet") + 1])
        # tricky here: we need to map 4 to 0, 3 to 1, 2 to 2 and 1 to 3
        name = name.replace(f"refinenet{layer_idx}", f"fusion_stage.layers.{abs(layer_idx - 4)}")
    if "out_conv" in name:
        name = name.replace("out_conv", "projection")
    if "resConfUnit1" in name:
        name = name.replace("resConfUnit1", "residual_layer1")
    if "resConfUnit2" in name:
        name = name.replace("resConfUnit2", "residual_layer2")
    if "conv1" in name:
        name = name.replace("conv1", "convolution1")
    if "conv2" in name:
        name = name.replace("conv2", "convolution2")
    # readout blocks
    if "pretrained.act_postprocess1.0.project.0" in name:
        name = name.replace("pretrained.act_postprocess1.0.project.0", "neck.reassemble_stage.readout_projects.0.0")
    if "pretrained.act_postprocess2.0.project.0" in name:
        name = name.replace("pretrained.act_postprocess2.0.project.0", "neck.reassemble_stage.readout_projects.1.0")
    if "pretrained.act_postprocess3.0.project.0" in name:
        name = name.replace("pretrained.act_postprocess3.0.project.0", "neck.reassemble_stage.readout_projects.2.0")
    if "pretrained.act_postprocess4.0.project.0" in name:
        name = name.replace("pretrained.act_postprocess4.0.project.0", "neck.reassemble_stage.readout_projects.3.0")
    # resize blocks
    if "pretrained.act_postprocess1.3" in name:
        name = name.replace("pretrained.act_postprocess1.3", "neck.reassemble_stage.layers.0.projection")
    if "pretrained.act_postprocess1.4" in name:
        name = name.replace("pretrained.act_postprocess1.4", "neck.reassemble_stage.layers.0.resize")
    if "pretrained.act_postprocess2.3" in name:
        name = name.replace("pretrained.act_postprocess2.3", "neck.reassemble_stage.layers.1.projection")
    if "pretrained.act_postprocess2.4" in name:
        name = name.replace("pretrained.act_postprocess2.4", "neck.reassemble_stage.layers.1.resize")
    if "pretrained.act_postprocess3.3" in name:
        name = name.replace("pretrained.act_postprocess3.3", "neck.reassemble_stage.layers.2.projection")
    if "pretrained.act_postprocess4.3" in name:
        name = name.replace("pretrained.act_postprocess4.3", "neck.reassemble_stage.layers.3.projection")
    if "pretrained.act_postprocess4.4" in name:
        name = name.replace("pretrained.act_postprocess4.4", "neck.reassemble_stage.layers.3.resize")
    if "pretrained" in name:
        name = name.replace("pretrained", "dpt")
    if "bn" in name:
        name = name.replace("bn", "batch_norm")
    if "head" in name:
        name = name.replace("head", "head.head")
    if "encoder.norm" in name:
        name = name.replace("encoder.norm", "layernorm")
    if "auxlayer" in name:
        name = name.replace("auxlayer", "auxiliary_head.head")

    return name