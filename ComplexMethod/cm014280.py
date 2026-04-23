def _extract_distributed_info(
    gm: torch.fx.GraphModule,
) -> dict[str, dict[str, int]]:
    """
    Extract process group information from distributed ops in the graph.

    Returns a dict mapping group names to dicts with 'size' and 'rank' keys.
    Example: {'tp': {'size': 4, 'rank': 0}, 'dp': {'size': 2, 'rank': 0}}
    """
    from torch.distributed import GroupName
    from torch.fx.operator_schemas import normalize_function

    group_info: dict[str, dict[str, int]] = {}

    for node in gm.graph.nodes:
        if node.op != "call_function":
            continue
        if not isinstance(node.target, OpOverload):
            continue
        if node.target.namespace not in {"_c10d_functional", "c10d_functional"}:
            continue

        opt_args_kwargs = normalize_function(
            node.target,
            args=node.args,
            kwargs=node.kwargs,
            normalize_to_only_use_kwargs=True,
        )
        if opt_args_kwargs is None:
            continue
        _, kwargs = opt_args_kwargs

        group_name_ = kwargs.get("group_name")
        if not isinstance(group_name_, str):
            continue
        group_name = typing.cast(GroupName, group_name_)

        if group_name in group_info:
            continue

        from torch.distributed.distributed_c10d import (
            _get_group_size_by_name,
            _resolve_process_group,
        )

        group_size = _get_group_size_by_name(group_name)
        pg = _resolve_process_group(group_name)
        rank = pg.rank()
        group_info[group_name] = {"size": group_size, "rank": rank}

    return group_info