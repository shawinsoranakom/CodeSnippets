def make_all_device_put_sync(gm: torch.fx.GraphModule) -> int:
    """
    Convert all non_blocking=True device_put operations to non_blocking=False.

    Only performs the conversion if at least one non_blocking=True device_put
    exists in the graph.

    Returns:
        The number of device_put operations converted to sync.
    """
    g = gm.graph
    device_put_nodes = list(
        g.find_nodes(op="call_function", target=torch.ops.prims.device_put.default)
    )

    # Check if any non_blocking=True device_put exists
    has_async_device_put = False
    for n in device_put_nodes:
        opt_args_kwargs = normalize_function(
            n.target,
            args=n.args,
            kwargs=n.kwargs,
            normalize_to_only_use_kwargs=True,
        )
        if opt_args_kwargs is not None:
            _, kwargs = opt_args_kwargs
            if kwargs.get("non_blocking", False):
                has_async_device_put = True
                break

    if not has_async_device_put:
        return 0

    # Convert all non_blocking=True to non_blocking=False
    count = 0
    for n in device_put_nodes:
        opt_args_kwargs = normalize_function(
            n.target,
            args=n.args,
            kwargs=n.kwargs,
            normalize_to_only_use_kwargs=True,
        )
        if opt_args_kwargs is not None:
            _, kwargs = opt_args_kwargs
            if kwargs.get("non_blocking", False):
                kwargs["non_blocking"] = False
                n.args = n.args[0], kwargs["device"], kwargs["non_blocking"]
                n.kwargs = {}
                count += 1

    return count