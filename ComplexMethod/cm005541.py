def _prepare_attention_mask(model_kwargs: dict[str, Any], new_length: int, is_encoder_decoder: bool) -> dict[str, Any]:
    """Expands or crops the model's mask for decoding purposes, to the defined length"""

    mask_key = "decoder_attention_mask" if is_encoder_decoder else "attention_mask"
    if mask_key not in model_kwargs:
        return model_kwargs

    mask = model_kwargs[mask_key]
    mask_length_diff = new_length - mask.shape[1]

    if mask_length_diff < 0:
        model_kwargs[mask_key] = mask[:, :mask_length_diff]
    elif mask_length_diff > 0:
        model_kwargs[mask_key] = torch.cat([mask, mask.new_ones((mask.shape[0], mask_length_diff))], dim=-1)

    # Handle cross attention models
    if "cross_attention_mask" in model_kwargs:
        # Mllama case
        cross_mask = model_kwargs["cross_attention_mask"]
        if mask_length_diff < 0:
            model_kwargs["cross_attention_mask"] = cross_mask[:, :mask_length_diff]
        elif mask_length_diff > 0:
            new_mask = cross_mask[:, -1:, :, :].repeat(1, mask_length_diff, 1, 1)
            model_kwargs["cross_attention_mask"] = torch.cat([cross_mask, new_mask], dim=1)
    elif "image_attention_mask" in model_kwargs:
        # IDEFICS case
        cross_mask = model_kwargs["image_attention_mask"]
        if mask_length_diff < 0:
            model_kwargs["image_attention_mask"] = cross_mask[:, :mask_length_diff]
        elif mask_length_diff > 0:
            new_mask = cross_mask[:, -1:, :].repeat(1, mask_length_diff, 1)
            model_kwargs["image_attention_mask"] = torch.cat([cross_mask, new_mask], dim=1)

    return model_kwargs