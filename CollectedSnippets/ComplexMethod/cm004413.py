def _collect_original_backbone_states(model, pixel_values: torch.Tensor) -> BackboneVerificationOutputs:
    backbone = model.encoder.backbone
    hidden_states = (pixel_values - model.encoder.pixel_mean) / model.encoder.pixel_std

    rope = None
    if hasattr(backbone, "rope_embeddings"):
        rope = backbone.rope_embeddings(hidden_states)

    hidden_states = backbone.patch_embed(hidden_states)
    patch_embeddings = hidden_states.detach().clone()
    if rope is None:
        raise ValueError("Original model is missing rope embeddings")
    outputs = []
    mask_logits_list = []
    class_logits_list = []
    attn_mask = None

    for idx, block in enumerate(backbone.blocks):
        if idx == len(backbone.blocks) - model.num_blocks:
            query = model.q.weight[None, :, :].expand(hidden_states.shape[0], -1, -1)
            hidden_states = torch.cat((query, hidden_states), dim=1)

        if idx >= len(backbone.blocks) - model.num_blocks:
            norm_hidden_states = backbone.norm(hidden_states)
            mask_logits, class_logits = model._predict(norm_hidden_states)
            mask_logits_list.append(mask_logits)
            class_logits_list.append(class_logits)
            attn_mask = model._attn_mask(hidden_states, mask_logits, idx)

        attn_module = block.attention if hasattr(block, "attention") else block.attn
        attn_output = model._attn(attn_module, block.norm1(hidden_states), attn_mask, rope=rope)
        if hasattr(block, "layer_scale1"):
            hidden_states = hidden_states + block.layer_scale1(attn_output)
        else:
            hidden_states = hidden_states + block.ls1(attn_output)

        mlp_output = block.mlp(block.norm2(hidden_states))
        if hasattr(block, "layer_scale2"):
            hidden_states = hidden_states + block.layer_scale2(mlp_output)
        else:
            hidden_states = hidden_states + block.ls2(mlp_output)

        outputs.append(hidden_states)

    sequence_output = backbone.norm(hidden_states)
    mask_logits, class_logits = model._predict(sequence_output)
    mask_logits_list.append(mask_logits)
    class_logits_list.append(class_logits)

    return BackboneVerificationOutputs(
        patch_embeddings=patch_embeddings,
        rope_embeddings=rope,
        hidden_states=outputs,
        mask_logits=mask_logits_list,
        class_logits=class_logits_list,
        sequence_output=sequence_output,
    )