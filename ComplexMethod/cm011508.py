def cat_single_dim_strategy(
    op: OpOverload, args_schema: ArgsType, kwargs_schema: KwargsType
) -> list[list[Placement | _ShardingPlaceholder]]:
    input_list = args_schema[0]
    # unfortunate naming, but yes it's a TensorList input, and we represent it as a tuple of TensorMeta
    if not isinstance(input_list, (tuple, list)):
        raise AssertionError(type(input_list))
    if not all(isinstance(tm, TensorMeta) for tm in input_list):
        raise AssertionError

    if isinstance(input_list, list):
        input_list = tuple(input_list)

    num_inputs = len(input_list)
    ndim_set = {len(meta.shape) for meta in input_list}
    if len(ndim_set) not in (1, 2):
        raise AssertionError(
            "Expected all cat inputs to be the same ndim, except empty tensors"
        )
    if len(ndim_set) == 2:
        if 0 not in ndim_set:
            raise AssertionError
    common_ndim = max(ndim_set)
    cat_dim = cast(int, args_schema[1]) if len(args_schema) > 1 else 0
    cat_dim = normalize_dim(cat_dim, common_ndim)
    single_dim_strategies = []
    for i in range(common_ndim):
        if i != cat_dim:
            single_dim_strategies.append([_ShardingPlaceholder(i)] * (1 + num_inputs))
    # pyrefly: ignore [bad-argument-type]
    single_dim_strategies.append([Partial("sum")] * (1 + num_inputs))
    # pyrefly: ignore [bad-return]
    return single_dim_strategies