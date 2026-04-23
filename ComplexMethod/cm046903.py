def make_q_galore_param_groups(
    model: torch.nn.Module,
    lr: float = 1e-3,
    weight_decay: float = 0.0,
    rank: int = 256,
    update_proj_gap: int = 200,
    scale: float = 0.25,
    proj_quant: bool = True,
    proj_quant_group_size: int = -1,
    proj_quant_n_bit: int = 4,
    weight_quant: bool = False,
    stochastic_round: bool = True,
    weight_group_size: int = 128,
    cos_threshold: float = 0.4,
    gamma_proj: float = 2.0,
    queue_size: int = 5,
    target_modules: Optional[List[str]] = None,
) -> list:
    """Build param groups suitable for :class:`QGaLoreAdamW8bit`.

    Parameters matching ``target_modules`` (or the default set of attention
    and MLP projection names) are placed in the GaLore group.  All other
    trainable parameters go into the non-GaLore group.

    Args:
        model: The model whose parameters to partition.
        lr: Learning rate for all parameter groups.
        weight_decay: Weight decay coefficient.
        rank: GaLore projection rank.
        update_proj_gap: Steps between SVD recomputations.
        scale: Scaling factor for project-back.
        proj_quant: Quantize projection matrices.
        proj_quant_group_size: Group size for projection quantization.
        proj_quant_n_bit: Bit-width for projection quantization.
        weight_quant: Enable INT8 weight quantization for GaLore params.
        stochastic_round: Use stochastic rounding for weight quantization.
        weight_group_size: Group size for weight quantization.
        cos_threshold: Cosine similarity threshold for adaptive scheduling.
        gamma_proj: Multiplier for update_proj_gap when subspace is stable.
        queue_size: Rolling window size for stability tracking.
        target_modules: Module name substrings to match for GaLore.  If None,
            uses the default set of attention/MLP projection names.

    Returns:
        List of two param group dicts: ``[galore_group, non_galore_group]``.
    """
    targets = (
        set(target_modules) if target_modules is not None else _DEFAULT_GALORE_TARGETS
    )

    galore_params = []
    non_galore_params = []

    for name, param in model.named_parameters():
        if not param.requires_grad:
            continue

        # Check if any target module name appears as a component in the param name.
        # Exclude 1-D parameters (biases, norms) because GaLoreProjector.project
        # requires 2-D gradients.
        name_parts = name.split(".")
        is_galore = param.dim() >= 2 and any(t in name_parts for t in targets)

        if is_galore:
            galore_params.append(param)
        else:
            non_galore_params.append(param)

    groups = []

    if galore_params:
        groups.append(
            {
                "params": galore_params,
                "lr": lr,
                "weight_decay": weight_decay,
                "rank": rank,
                "update_proj_gap": update_proj_gap,
                "scale": scale,
                "proj_type": "std",
                "quant": proj_quant,
                "quant_group_size": proj_quant_group_size,
                "quant_n_bit": proj_quant_n_bit,
                "weight_quant": weight_quant,
                "stochastic_round": stochastic_round,
                "weight_group_size": weight_group_size,
                "cos_threshold": cos_threshold,
                "gamma_proj": gamma_proj,
                "queue_size": queue_size,
            }
        )

    if non_galore_params:
        groups.append(
            {
                "params": non_galore_params,
                "lr": lr,
                "weight_decay": weight_decay,
            }
        )

    return groups