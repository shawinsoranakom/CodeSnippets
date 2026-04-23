def reduction(
    size_hints,
    reduction_hint=False,
    triton_meta=None,
    filename=None,
    inductor_meta=None,
    return_configs=False,
):
    """args to @triton.heuristics()"""
    inductor_meta = {} if inductor_meta is None else inductor_meta
    inductor_meta["reduction_hint"] = reduction_hint
    if inductor_meta.get("no_x_dim"):
        size_hints["x"] = 1

    configs = _handle_combo_kernel_per_subkernel_blocks(
        size_hints,
        inductor_meta,
        triton_meta,
        filename=filename,
        reduction_hint=reduction_hint,
    )
    if configs is not None:
        return cached_autotune(
            None,
            configs,
            triton_meta=triton_meta,
            inductor_meta=inductor_meta,
            heuristic_type=HeuristicType.REDUCTION,
            filename=filename,
        )

    assert triton_meta is not None

    num_dynamic = 0
    for k in triton_meta["signature"]:
        if "ks" in k:
            num_dynamic += 1

    configs = _reduction_configs(
        size_hints=size_hints,
        inductor_meta=inductor_meta,
        triton_meta=triton_meta,
        num_dynamic=num_dynamic,
    )

    configs = _maybe_filter_configs_for_tma_restrictions(inductor_meta, configs)
    configs = filter_reduction_configs_for_determinism(inductor_meta, configs)

    if return_configs:
        return configs

    return cached_autotune(
        size_hints,
        configs=configs,
        triton_meta=triton_meta,
        inductor_meta=inductor_meta,
        heuristic_type=HeuristicType.REDUCTION,
        filename=filename,
    )