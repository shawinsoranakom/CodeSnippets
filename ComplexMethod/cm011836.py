def with_effects(token, op, *args, **kwargs):
    """
    We lower the operator directly, and then we add StarDep dependencies to all
    the newly created nodes in the graph.
    """
    from torch._higher_order_ops.effects import _get_effect, _get_schema

    # Get effect type
    effect_type = _get_effect(op)
    if effect_type is None and op is torch.ops.higher_order.invoke_subgraph:
        from torch._guards import InvokeSubgraphCache, TracingContext

        tracing_ctx = TracingContext.try_get()
        if tracing_ctx:
            invoke_subgraph_cache = tracing_ctx.hop_dispatch_set_cache.get_cache(
                torch.ops.higher_order.invoke_subgraph
            )
            if invoke_subgraph_cache:
                assert isinstance(invoke_subgraph_cache, InvokeSubgraphCache)
                # args[1] is identifier
                effects = invoke_subgraph_cache.get_effects(args[1])
                if effects:
                    assert len(effects) == 1, "Multiple effects NYI"
                    effect_type = next(iter(effects))

    # Track operations before
    operation_len = len(V.graph.operations)

    # Lower the op
    if op in lowerings:
        result = lowerings[op](*args, **kwargs)
        # Realize so that we can get the ops to show up in V.graph.operations
        pytree.tree_map_only(TensorBox, lambda a: a.realize(), result)
    else:

        def wrap_tensors(x):
            return x.wrap_for_lowering() if isinstance(x, ir.IRNode) else x

        result = pytree.tree_map(
            wrap_tensors, ir.FallbackKernel.create(op, *args, **kwargs)
        )

    # Get all the operations created during the lowering above, and add StarDeps
    # to the previous node with the same effect
    assert len(V.graph.operations[operation_len:]) > 0, (
        f"No operation nodes were generated when lowering effectful operator {op}."
    )
    if effect_type:
        prev_effect_buffer = V.graph.effectful_ops.get(effect_type)
        for new_op in V.graph.operations[operation_len:]:
            # Patch has_side_effects to return True
            new_op.has_side_effects = lambda: True  # pyrefly: ignore[missing-attribute]
            if prev_effect_buffer:
                op_name = new_op.get_name()  # pyrefly: ignore[missing-attribute]
                V.graph.additional_star_deps[op_name].add(prev_effect_buffer.get_name())
        # Update the effectful ops chain to point to the latest operation
        V.graph.effectful_ops[effect_type] = (
            new_op  # pyrefly: ignore[unsupported-operation]
        )

    try:

        def convert_ir_to_value(a):
            if isinstance(a, ir.TorchBindObject):
                return a.get_value()
            elif isinstance(a, TensorBox):
                # TensorBox wraps StorageBox, which wraps the actual buffer
                # We need to get the example tensor from the inner buffer
                try:
                    storage = a.data
                    if hasattr(storage, "data") and hasattr(
                        storage.data, "get_example"
                    ):
                        return storage.data.get_example()
                except (AttributeError, NotImplementedError):
                    pass
                # Fall back to returning the TensorBox itself if get_example fails
                return a
            return a

        schema_args, schema_kwargs = pytree.tree_map(
            convert_ir_to_value, (args, kwargs)
        )
        schema = _get_schema(op, schema_args, schema_kwargs)
    except RuntimeError as e:
        error_msg = str(e)
        log.warning(
            "Failed to get schema for %s: %s. Assuming list output", op, error_msg
        )
        if isinstance(result, (tuple, list)):
            return (token, *result)
        else:
            return (token, result)

    if len(schema.returns) == 0:
        return (token, result)
    elif len(schema.returns) == 1:
        return (token, result)
    else:
        return (token, *result)