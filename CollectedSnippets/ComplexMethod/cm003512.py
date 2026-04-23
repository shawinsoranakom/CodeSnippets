def fuse_experts(
    expert_weights: dict[tuple, torch.Tensor],
    n_experts: int,
    has_vision: bool,
    output_fp8: bool,
) -> dict[str, torch.Tensor]:
    r"""Fuse per-expert weights across all layers."""
    prefix = "model.language_model" if has_vision else "model"

    grouped: dict[tuple, dict[int, torch.Tensor]] = defaultdict(dict)
    for (layer_idx, expert_idx, param_type, suffix), tensor in expert_weights.items():
        grouped[(layer_idx, param_type, suffix)][int(expert_idx)] = tensor

    consumed_keys: set[tuple] = set()
    result: dict[str, torch.Tensor] = {}
    layers = sorted({layer_idx for (layer_idx, _, _) in grouped})

    for layer_idx in layers:
        base = f"{prefix}.layers.{layer_idx}.mlp.experts"

        w1_weight_key = (layer_idx, "w1", "weight")
        assert w1_weight_key in grouped, f"Layer {layer_idx}: missing w1 weights"
        assert len(grouped[w1_weight_key]) == n_experts, (
            f"Layer {layer_idx}: expected {n_experts} w1 experts, got {len(grouped[w1_weight_key])}"
        )

        for param in ("w1", "w2", "w3"):
            for suffix in ("weight", "qscale_weight", "qscale_act"):
                key = (layer_idx, param, suffix)
                if key in grouped:
                    consumed_keys.add(key)

        layer_result = _fuse_experts_for_layer(grouped, layer_idx, n_experts, base, output_fp8)

        result.update(layer_result)

    unconsumed = set(grouped.keys()) - consumed_keys
    assert not unconsumed, f"Unconsumed expert groups: {unconsumed}"

    return result