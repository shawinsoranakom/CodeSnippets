def merge_all_gather_bucket(
    g: torch.fx.Graph,
    ag_nodes: list[torch.fx.Node],
    mode: BucketMode | None = None,
    insert_before: torch.fx.Node | None = None,
    wait_insertion_point: torch.fx.Node | None = None,
) -> tuple[list[torch.fx.Node], dict[torch.fx.Node, torch.fx.Node]]:
    mode = mode or _default_bucket_mode()
    from torch.distributed.distributed_c10d import _resolve_process_group

    ag0 = ag_nodes[0]
    _, group_size, group_name = ag0.args
    assert isinstance(group_name, str)
    _ag_dtypes: list[torch.dtype] = []  # type: ignore[name-defined]

    for n in ag_nodes:
        assert n.args[1] == group_size and n.args[2] == group_name
        _ag_dtypes.append(n.meta["val"].dtype)

    bucket_dtype = pick_bucket_dtype(_ag_dtypes)

    # Choose merge function based on mode
    ag_merge_fn = all_gather_merge_fn_to_trace
    if mode == "coalesced":
        logger.info("coalesced bucket_mode not supported for all_gather, using default")
    elif mode and "custom_ops" in mode:
        ag_merge_fn = all_gather_merge_fn_to_trace_custom_ops  # type: ignore[assignment]

    # Process bucket with lazy input collection
    # pyrefly: ignore [bad-argument-type]
    rank: int = dist.get_rank(_resolve_process_group(group_name))

    def create_trace_args(bucket_ins: list[torch.fx.Node]) -> tuple[Any, ...]:
        return (
            pytree.tree_map(lambda node: node.meta["val"], bucket_ins),
            group_size,
            group_name,
            bucket_dtype,
            _ag_dtypes,
            rank,
        )

    return process_collective_bucket(
        g,
        ag_nodes,
        ag_merge_fn,
        create_trace_args,
        wait_insertion_point=wait_insertion_point,
    )