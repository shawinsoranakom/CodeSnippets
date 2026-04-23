def rename_key(name):
    # Transformer backbone
    if "core.core.pretrained.model.blocks" in name:
        name = name.replace("core.core.pretrained.model.blocks", "backbone.encoder.layer")
    if "core.core.pretrained.model.patch_embed.proj" in name:
        name = name.replace(
            "core.core.pretrained.model.patch_embed.proj", "backbone.embeddings.patch_embeddings.projection"
        )
    if "core.core.pretrained.model.cls_token" in name:
        name = name.replace("core.core.pretrained.model.cls_token", "backbone.embeddings.cls_token")
    if "norm1" in name and "patch_transformer" not in name:
        name = name.replace("norm1", "layernorm_before")
    if "norm2" in name and "patch_transformer" not in name:
        name = name.replace("norm2", "layernorm_after")
    if "mlp.fc1" in name:
        name = name.replace("mlp.fc1", "intermediate.dense")
    if "mlp.fc2" in name:
        name = name.replace("mlp.fc2", "output.dense")
    if "gamma_1" in name:
        name = name.replace("gamma_1", "lambda_1")
    if "gamma_2" in name:
        name = name.replace("gamma_2", "lambda_2")
    if "attn.proj" in name:
        name = name.replace("attn.proj", "attention.output.dense")
    if "attn.relative_position_bias_table" in name:
        name = name.replace(
            "attn.relative_position_bias_table",
            "attention.attention.relative_position_bias.relative_position_bias_table",
        )
    if "attn.relative_position_index" in name:
        name = name.replace(
            "attn.relative_position_index", "attention.attention.relative_position_bias.relative_position_index"
        )

    # activation postprocessing (readout projections + resize blocks)
    if "core.core.pretrained.act_postprocess1.0.project" in name:
        name = name.replace(
            "core.core.pretrained.act_postprocess1.0.project", "neck.reassemble_stage.readout_projects.0"
        )
    if "core.core.pretrained.act_postprocess2.0.project" in name:
        name = name.replace(
            "core.core.pretrained.act_postprocess2.0.project", "neck.reassemble_stage.readout_projects.1"
        )
    if "core.core.pretrained.act_postprocess3.0.project" in name:
        name = name.replace(
            "core.core.pretrained.act_postprocess3.0.project", "neck.reassemble_stage.readout_projects.2"
        )
    if "core.core.pretrained.act_postprocess4.0.project" in name:
        name = name.replace(
            "core.core.pretrained.act_postprocess4.0.project", "neck.reassemble_stage.readout_projects.3"
        )

    if "core.core.pretrained.act_postprocess1.3" in name:
        name = name.replace("core.core.pretrained.act_postprocess1.3", "neck.reassemble_stage.layers.0.projection")
    if "core.core.pretrained.act_postprocess2.3" in name:
        name = name.replace("core.core.pretrained.act_postprocess2.3", "neck.reassemble_stage.layers.1.projection")
    if "core.core.pretrained.act_postprocess3.3" in name:
        name = name.replace("core.core.pretrained.act_postprocess3.3", "neck.reassemble_stage.layers.2.projection")
    if "core.core.pretrained.act_postprocess4.3" in name:
        name = name.replace("core.core.pretrained.act_postprocess4.3", "neck.reassemble_stage.layers.3.projection")

    if "core.core.pretrained.act_postprocess1.4" in name:
        name = name.replace("core.core.pretrained.act_postprocess1.4", "neck.reassemble_stage.layers.0.resize")
    if "core.core.pretrained.act_postprocess2.4" in name:
        name = name.replace("core.core.pretrained.act_postprocess2.4", "neck.reassemble_stage.layers.1.resize")
    if "core.core.pretrained.act_postprocess4.4" in name:
        name = name.replace("core.core.pretrained.act_postprocess4.4", "neck.reassemble_stage.layers.3.resize")

    # scratch convolutions
    if "core.core.scratch.layer1_rn.weight" in name:
        name = name.replace("core.core.scratch.layer1_rn.weight", "neck.convs.0.weight")
    if "core.core.scratch.layer2_rn.weight" in name:
        name = name.replace("core.core.scratch.layer2_rn.weight", "neck.convs.1.weight")
    if "core.core.scratch.layer3_rn.weight" in name:
        name = name.replace("core.core.scratch.layer3_rn.weight", "neck.convs.2.weight")
    if "core.core.scratch.layer4_rn.weight" in name:
        name = name.replace("core.core.scratch.layer4_rn.weight", "neck.convs.3.weight")

    # fusion layers
    # tricky here: mapping = {1:3, 2:2, 3:1, 4:0}
    if "core.core.scratch.refinenet1" in name:
        name = name.replace("core.core.scratch.refinenet1", "neck.fusion_stage.layers.3")
    if "core.core.scratch.refinenet2" in name:
        name = name.replace("core.core.scratch.refinenet2", "neck.fusion_stage.layers.2")
    if "core.core.scratch.refinenet3" in name:
        name = name.replace("core.core.scratch.refinenet3", "neck.fusion_stage.layers.1")
    if "core.core.scratch.refinenet4" in name:
        name = name.replace("core.core.scratch.refinenet4", "neck.fusion_stage.layers.0")

    if "resConfUnit1" in name:
        name = name.replace("resConfUnit1", "residual_layer1")

    if "resConfUnit2" in name:
        name = name.replace("resConfUnit2", "residual_layer2")

    if "conv1" in name:
        name = name.replace("conv1", "convolution1")

    if "conv2" in name and "residual_layer" in name:
        name = name.replace("conv2", "convolution2")

    if "out_conv" in name:
        name = name.replace("out_conv", "projection")

    # relative depth estimation head
    if "core.core.scratch.output_conv.0" in name:
        name = name.replace("core.core.scratch.output_conv.0", "relative_head.conv1")

    if "core.core.scratch.output_conv.2" in name:
        name = name.replace("core.core.scratch.output_conv.2", "relative_head.conv2")

    if "core.core.scratch.output_conv.4" in name:
        name = name.replace("core.core.scratch.output_conv.4", "relative_head.conv3")

    # patch transformer
    if "patch_transformer" in name:
        name = name.replace("patch_transformer", "metric_head.patch_transformer")

    if "mlp_classifier.0" in name:
        name = name.replace("mlp_classifier.0", "metric_head.mlp_classifier.linear1")
    if "mlp_classifier.2" in name:
        name = name.replace("mlp_classifier.2", "metric_head.mlp_classifier.linear2")

    if "projectors" in name:
        name = name.replace("projectors", "metric_head.projectors")

    if "seed_bin_regressors" in name:
        name = name.replace("seed_bin_regressors", "metric_head.seed_bin_regressors")

    if "seed_bin_regressor" in name and "seed_bin_regressors" not in name:
        name = name.replace("seed_bin_regressor", "metric_head.seed_bin_regressor")

    if "seed_projector" in name:
        name = name.replace("seed_projector", "metric_head.seed_projector")

    if "_net.0" in name:
        name = name.replace("_net.0", "conv1")

    if "_net.2" in name:
        name = name.replace("_net.2", "conv2")

    if "attractors" in name:
        name = name.replace("attractors", "metric_head.attractors")

    if "conditional_log_binomial" in name:
        name = name.replace("conditional_log_binomial", "metric_head.conditional_log_binomial")

    # metric depth estimation head
    if "conv2" in name and "metric_head" not in name and "attractors" not in name and "relative_head" not in name:
        name = name.replace("conv2", "metric_head.conv2")

    if "transformer_encoder.layers" in name:
        name = name.replace("transformer_encoder.layers", "transformer_encoder")

    return name