def convert_state_dict(
    original_state_dict: dict[str, torch.Tensor],
    text_renamings: list[WeightRenaming],
    vision_renamings: list[WeightRenaming],
    total_keys_seen: set[str],
    vision_config: PixtralVisionConfig | None = None,
    is_fp8_source: bool = False,
    output_bf16: bool = False,
) -> tuple[dict[str, torch.Tensor], dict[tuple, torch.Tensor]]:
    r"""Rename and optionally descale one shard of the original state dict."""
    new_dict: dict[str, torch.Tensor] = {}
    expert_weights: dict[tuple, torch.Tensor] = {}

    for old_key, tensor in original_state_dict.items():
        assert old_key not in total_keys_seen, f"Duplicate key across shards: {old_key}"
        total_keys_seen.add(old_key)

        match = EXPERT_KEY_PATTERN.match(old_key)
        if match:
            layer_idx, expert_idx, param_type, suffix = int(match[1]), int(match[2]), match[3], match[4]
            expert_weights[(layer_idx, expert_idx, param_type, suffix)] = tensor
            continue

        if output_bf16 and is_fp8_source:
            if old_key.endswith((".qscale_act", ".qscale_weight")):
                continue
            if old_key.endswith(".weight"):
                scale_key = old_key.rsplit(".weight", 1)[0] + ".qscale_weight"
                if scale_key in original_state_dict:
                    tensor = _descale_fp8_to_bf16(tensor, original_state_dict[scale_key])

        new_key = _rename_key(old_key, text_renamings, vision_renamings)

        if vision_config is not None and "vision_tower" in new_key:
            tensor = _maybe_permute_vision_rope(new_key, tensor, vision_config)

        new_dict[new_key] = tensor

    return new_dict, expert_weights