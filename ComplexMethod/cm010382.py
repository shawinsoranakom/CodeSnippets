def auto_functionalized_v2_proxy(
    mode,
    _mutable_op: _MutableOpType,
    **kwargs: Any,
) -> tuple[Any, tuple[Tensor, ...]]:
    if isinstance(_mutable_op, HigherOrderOperator):
        # Note [materialize callable inputs as graph]
        # Below code materializes the callable inputs to the hop as graph modules.
        # kwargs may contain general callables, that are not proxable e.g. FunctionWithNoFreeVars
        # this could happen when we auto_functionalize the backward of the hop,
        # where backward fn is a callablle that wraps forward graph module.
        # This function materialize the callable args according to the schema of the hop.

        # We cannot materialize the callables in kwargs directly because the inputs to callable
        # vary from hops to hop. To make the materialiation process generic to all hops,
        # we trace a function that wraps the hop and let each hop itself figure out how to trace
        # its callable inputs. Then we look at the schema of the traced hop node and replace the
        # callable in original kwarg with the traced subgraphs.
        #
        # Specifically, we first trace a wrapped_fn that calls into the hop. Then we look for the
        # hop node in the traced graph and graph module inputs to the hop. Finally, we replace the
        # original kwarg's callable with the graph module.
        all_bases = kwargs.get("_all_bases", [])
        _only_clone_these_bases = kwargs.get("_only_clone_these_bases")
        if _only_clone_these_bases is None:
            _only_clone_these_bases = tuple(range(len(all_bases)))

        schema = pytree.tree_unflatten([], kwargs.get("_op_schema")).schema  # type: ignore[arg-type]
        new_kwargs, _ = _generate_new_op_kwargs_from_bases(
            schema,
            {k: v for k, v in kwargs.items() if k not in ("_all_bases", "_op_schema")},
            all_bases,
            _only_clone_these_bases,
            _is_out=False,
        )

        _, materialized_kwargs = materialize_callable_in_args(
            HopInstance(_mutable_op, schema), tuple(), new_kwargs
        )

        # Only replace the callables in kwargs with the materialized subgraphs.
        # The rest of the kwargs are kept unchanged.
        subgraph_arg_names = {
            arg_info.name
            for arg_info in schema.arguments
            if isinstance(arg_info.type, torch._C.AnyType)
        }
        for k, v in kwargs.items():
            if k in subgraph_arg_names and callable(v):
                if k not in materialized_kwargs or not isinstance(
                    materialized_kwargs[k], torch.fx.GraphModule
                ):
                    raise AssertionError(
                        f"Expected {k} to be in materialized_kwargs as a GraphModule"
                    )
                kwargs[k] = materialized_kwargs[k]

    with disable_proxy_modes_tracing():
        out = auto_functionalized_v2(_mutable_op, **kwargs)

    proxy_kwargs = pytree.tree_map(mode.tracer.unwrap_proxy, kwargs)

    if isinstance(_mutable_op, HigherOrderOperator):

        def _maybe_register_subgraph(val: Any):
            if isinstance(val, torch.fx.GraphModule):
                _, graph_name = unique_graph_id(
                    mode, prefix="auto_functionalized_subgraph"
                )
                mode.tracer.root.register_module(graph_name, val)
                return val
            return val

        proxy_kwargs = pytree.tree_map(_maybe_register_subgraph, proxy_kwargs)

    out_proxy = mode.tracer.create_proxy(
        "call_function",
        auto_functionalized_v2,
        (_mutable_op,),
        proxy_kwargs,
    )
    result = track_tensor_tree(out, out_proxy, constant=None, tracer=mode.tracer)
    return result