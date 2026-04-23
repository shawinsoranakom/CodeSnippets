def scaled_mm_single_dim_strategy(
    op: OpOverload, args_schema: ArgsType, kwargs_schema: KwargsType
) -> list[list[Placement | _ShardingPlaceholder]]:
    scale_self_meta = args_schema[2]
    scale_mat2_meta = args_schema[3]
    if not isinstance(scale_self_meta, TensorMeta):
        raise AssertionError
    if not isinstance(scale_mat2_meta, TensorMeta):
        raise AssertionError
    if args_schema[4] is not None:
        raise AssertionError("_scaled_mm on DTensors doesn't support bias")
    if args_schema[5] is not None:
        raise AssertionError("_scaled_mm on DTensors doesn't support scale_result")

    # "mk,kn->mn": self_contracting_dim=1, mat2_contracting_dim=0
    base_strategies = gen_single_dim_einsum_strategies("mk,kn->mn")
    result = []
    for strat in base_strategies:
        # strat is [output, self, mat2]; derive scale placements
        scale_self_p = _scaled_mm_scale_placement(
            strat[1], scale_self_meta.shape, contracting_dim=1
        )
        scale_mat2_p = _scaled_mm_scale_placement(
            strat[2], scale_mat2_meta.shape, contracting_dim=0
        )
        if scale_self_p is None or scale_mat2_p is None:
            continue
        result.append(strat + [scale_self_p, scale_mat2_p])
    return result