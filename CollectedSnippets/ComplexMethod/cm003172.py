def convert_state_dict(metaclip_state_dict: dict[str, torch.Tensor]) -> dict[str, torch.Tensor]:
    """Convert MetaCLIP state dict to Hugging Face format."""
    print("Converting state dict...")

    hf_state_dict = {}

    for key, value in metaclip_state_dict.items():
        new_key = key

        # Handle specific mappings first before general prefix replacements
        if key == "visual.proj":
            new_key = "visual_projection.weight"
            # Don't transpose! MetaCLIP: x @ proj, HF: Linear(x) = x @ weight.T
            # So we want weight.T = proj, which means weight = proj.T
            # But since we're storing proj as weight, we need proj.T
            value = value.T  # This gives us the correct orientation for Linear layer
        elif key == "text_projection":
            new_key = "text_projection.weight"
            # Same logic as visual projection
            value = value.T
        elif key == "token_embedding.weight":
            new_key = "text_model.embeddings.token_embedding.weight"
        elif key == "positional_embedding":
            new_key = "text_model.embeddings.position_embedding.weight"
        elif key == "ln_final.weight":
            new_key = "text_model.final_layer_norm.weight"
        elif key == "ln_final.bias":
            new_key = "text_model.final_layer_norm.bias"
        # Vision encoder mappings
        elif key.startswith("visual."):
            new_key = key.replace("visual.", "vision_model.")

            # Handle specific vision model components
            if "conv1" in new_key:
                new_key = new_key.replace("conv1", "embeddings.patch_embedding")
            elif "class_embedding" in new_key:
                new_key = new_key.replace("class_embedding", "embeddings.class_embedding")
            elif "positional_embedding" in new_key:
                new_key = new_key.replace("positional_embedding", "embeddings.position_embedding.weight")
            elif "ln_pre" in new_key:
                new_key = new_key.replace("ln_pre", "pre_layrnorm")
            elif "ln_post" in new_key:
                new_key = new_key.replace("ln_post", "post_layernorm")
            elif "transformer.resblocks" in new_key:
                new_key = new_key.replace("transformer.resblocks", "encoder.layers")
                # Handle attention and MLP mappings within transformer blocks
                if "attn.in_proj" in new_key:
                    # Split the in_proj into q, k, v projections
                    if "weight" in new_key:
                        # We'll handle this later in a special case
                        continue
                    elif "bias" in new_key:
                        continue
                elif "attn.out_proj" in new_key:
                    new_key = new_key.replace("attn.out_proj", "self_attn.out_proj")
                elif "ln_1" in new_key:
                    new_key = new_key.replace("ln_1", "layer_norm1")
                elif "ln_2" in new_key:
                    new_key = new_key.replace("ln_2", "layer_norm2")
                elif "mlp.c_fc" in new_key:
                    new_key = new_key.replace("mlp.c_fc", "mlp.fc1")
                elif "mlp.c_proj" in new_key:
                    new_key = new_key.replace("mlp.c_proj", "mlp.fc2")

        # Text encoder mappings
        elif key.startswith("transformer."):
            new_key = key.replace("transformer.", "text_model.encoder.")

            if "resblocks" in new_key:
                new_key = new_key.replace("resblocks", "layers")
                # Similar mappings as vision transformer
                if "attn.in_proj" in new_key:
                    continue  # Handle separately
                elif "attn.out_proj" in new_key:
                    new_key = new_key.replace("attn.out_proj", "self_attn.out_proj")
                elif "ln_1" in new_key:
                    new_key = new_key.replace("ln_1", "layer_norm1")
                elif "ln_2" in new_key:
                    new_key = new_key.replace("ln_2", "layer_norm2")
                elif "mlp.c_fc" in new_key:
                    new_key = new_key.replace("mlp.c_fc", "mlp.fc1")
                elif "mlp.c_proj" in new_key:
                    new_key = new_key.replace("mlp.c_proj", "mlp.fc2")

        hf_state_dict[new_key] = value

    # Handle in_proj weights separately (split into q, k, v)
    for key, value in metaclip_state_dict.items():
        if "attn.in_proj_weight" in key:
            # Split the combined qkv weight into separate q, k, v weights
            dim = value.shape[0] // 3
            q_weight = value[:dim]
            k_weight = value[dim : 2 * dim]
            v_weight = value[2 * dim :]

            base_key = key.replace("attn.in_proj_weight", "")
            if key.startswith("visual."):
                base_key = base_key.replace("visual.transformer.resblocks", "vision_model.encoder.layers")
            else:
                base_key = base_key.replace("transformer.resblocks", "text_model.encoder.layers")

            hf_state_dict[f"{base_key}self_attn.q_proj.weight"] = q_weight
            hf_state_dict[f"{base_key}self_attn.k_proj.weight"] = k_weight
            hf_state_dict[f"{base_key}self_attn.v_proj.weight"] = v_weight

        elif "attn.in_proj_bias" in key:
            # Split the combined qkv bias into separate q, k, v biases
            dim = value.shape[0] // 3
            q_bias = value[:dim]
            k_bias = value[dim : 2 * dim]
            v_bias = value[2 * dim :]

            base_key = key.replace("attn.in_proj_bias", "")
            if key.startswith("visual."):
                base_key = base_key.replace("visual.transformer.resblocks", "vision_model.encoder.layers")
            else:
                base_key = base_key.replace("transformer.resblocks", "text_model.encoder.layers")

            hf_state_dict[f"{base_key}self_attn.q_proj.bias"] = q_bias
            hf_state_dict[f"{base_key}self_attn.k_proj.bias"] = k_bias
            hf_state_dict[f"{base_key}self_attn.v_proj.bias"] = v_bias

    return hf_state_dict