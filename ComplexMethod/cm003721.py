def convert_clip_backbone(flax_params, torch_config):
    torch_model = CLIP(**torch_config)
    torch_model.eval()
    torch_clip_params = torch_model.state_dict()

    flax_clip_params = flatten_nested_dict(flax_params["backbone"]["clip"])
    new_torch_params = {}

    for flax_key, v in flax_clip_params.items():
        torch_key = flax_key.replace("/", ".")
        torch_key = torch_key.replace("text.token_embedding.embedding", "token_embedding.kernel")

        if (
            torch_key.startswith("text.transformer")
            or torch_key.startswith("text.text_projection")
            or torch_key.startswith("text.ln_final")
            or torch_key.startswith("text.positional_embedding")
        ):
            torch_key = torch_key[5:]

        torch_key = torch_key.replace("text_projection.kernel", "text_projection")
        torch_key = torch_key.replace("visual.proj.kernel", "visual.proj")
        torch_key = torch_key.replace(".scale", ".weight")
        torch_key = torch_key.replace(".kernel", ".weight")

        if "conv" in torch_key or "downsample.0.weight" in torch_key:
            v = v.transpose(3, 2, 0, 1)

        elif "weight" in torch_key and v.ndim == 2 and "embedding" not in torch_key:
            # Fully connected layers are transposed, embeddings are not
            v = v.T

        new_torch_params[torch_key] = v

    attn_params = _convert_attn_layers(new_torch_params)
    new_torch_params.update(attn_params)
    attn_params = {}

    # Copy flax CLIP backbone params to PyTorch params
    for name, param in new_torch_params.items():
        if name in torch_clip_params:
            new_param = torch.from_numpy(param)
            torch_clip_params[name].copy_(new_param)
        else:
            attn_params[name] = param

    return torch_clip_params, torch_model, attn_params