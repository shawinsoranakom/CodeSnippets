def materialize_callable_in_args(op: HopInstance, args, kwargs):
    schema = op._schema
    hop = op._op
    flat_args, flat_spec = pytree.tree_flatten((args, kwargs))

    def wrapped_fn(*flat_args):
        return call_op(op, args, kwargs)

    # We need to trace the higher order op in order to materilaize the callable inputs that
    # are a callable (e.g. after functionalization key)
    gm = reenter_make_fx(wrapped_fn)(*flat_args)
    hop_node = gm.graph.find_nodes(op="call_function", target=hop)[0]
    arg_proxies = pytree.tree_leaves((hop_node.args, hop_node.kwargs))
    if not isinstance(schema, torch._C.FunctionSchema) or len(arg_proxies) != len(
        schema.arguments
    ):
        raise AssertionError(
            f"Expected FunctionSchema with {len(arg_proxies)} arguments"
        )

    # call_op preserves ordering of proxies via schema
    materialized_args = []
    for i, proxy in enumerate(arg_proxies):
        if (
            isinstance(proxy, torch.fx.Node)
            and proxy.op == "get_attr"
            and isinstance(getattr(gm, proxy.target), torch.fx.GraphModule)  # type: ignore[arg-type]
        ):
            if not callable(flat_args[i]):
                raise AssertionError(
                    f"Expected flat_args[{i}] to be callable for {schema}"
                )
            materialized_args.append(getattr(gm, proxy.target))  # type: ignore[arg-type]
        else:
            materialized_args.append(flat_args[i])

    return pytree.tree_unflatten(materialized_args, flat_spec)