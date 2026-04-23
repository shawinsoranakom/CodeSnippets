def stamp_out_subgraph(
    tx: "InstructionTranslator",
    fingerprint: InputFingerprint,
    cached: InvokeSubgraphReuseEntry,
) -> VariableTracker:
    """Emit a new invoke_subgraph call by stamping out a cached subgraph.

    Sources in the cached entry are parameterized: they refer to the original
    call's sources and must be rewritten to the current call's sources via
    source replacement before we can look up or create the corresponding
    graph placeholders.
    """
    from torch._dynamo.variables.builder import VariableBuilder
    from torch._dynamo.variables.higher_order_ops import add_call_function, make_attr

    flat_proxies = get_flat_proxies(fingerprint)
    new_arg_sources = fingerprint.arg_sources

    source_replacement = build_source_replacement(cached.arg_sources, new_arg_sources)

    new_lifted_args = []
    # Shared resolution context so get_value memoizes intermediate results
    # (e.g. L['self'].layers) across all freevars in this stamp-out.
    resolve_globals: dict[str, Any] = {
        "G": tx.output.root_tx.f_globals,
        "L": tx.output.root_tx.f_locals,
    }
    resolve_locals: dict[str, Any] = {}
    resolve_cache: dict[Source, Any] = {}

    # Find the args for the about-to-be-inserted invoke_subgraph call.
    for subgraph_input in cached.subgraph_input_mapping:
        if isinstance(subgraph_input, LiftedUserArg):
            new_lifted_args.append(flat_proxies[subgraph_input.index])
        elif isinstance(subgraph_input, LiftedBoundSymbol):
            from torch._dynamo.output_graph import LazyProxy

            proxy = tx.output.current_tracer.bound_symbols[subgraph_input.expr]
            if isinstance(proxy, LazyProxy):
                proxy = proxy()
                tx.output.current_tracer.bound_symbols[subgraph_input.expr] = proxy
            new_lifted_args.append(proxy)
        elif isinstance(subgraph_input, LiftedSyntheticObject):
            ctor_args = subgraph_input.ctor_args
            ctor_arg_sources = subgraph_input.ctor_arg_sources
            if ctor_arg_sources and source_replacement:
                new_ctor_args = []
                new_ctor_arg_sources = []
                for val, arg_src in zip(ctor_args, ctor_arg_sources):
                    if arg_src is not None:
                        new_src = arg_src.clone(lambda s: source_replacement.get(s, s))
                        val = new_src.get_value(
                            resolve_globals, resolve_locals, resolve_cache
                        )
                        arg_src = new_src
                    new_ctor_args.append(val)
                    new_ctor_arg_sources.append(arg_src)
                ctor_args = tuple(new_ctor_args)
                ctor_arg_sources = tuple(new_ctor_arg_sources)
            vt = tx.output.synthetic_graph_input(
                subgraph_input.ctor_fn, ctor_args, ctor_arg_sources
            )
            new_lifted_args.append(vt.as_proxy())
        elif isinstance(subgraph_input, LiftedCapturedSource):
            new_source = subgraph_input.source
            if source_replacement:
                new_source = new_source.clone(lambda s: source_replacement.get(s, s))
            # VariableBuilder deduplicates via input_source_to_var,
            # so this reuses existing graph placeholders automatically.
            value = new_source.get_value(resolve_globals, resolve_locals, resolve_cache)
            vt = VariableBuilder(tx, new_source)(value)
            new_lifted_args.append(vt.as_proxy())

    # Generate fake tensor outputs
    assert tx.fake_mode is not None
    with tx.fake_mode:
        example_value = tuple(
            torch.empty_strided(
                shape,
                stride,
                dtype=dtype,
                device=device,
                requires_grad=req_grad,
            )
            for shape, stride, dtype, device, req_grad in cached.output_metadata
        )

    # Install the invoke_subgraph call
    body_node = make_attr(tx, cached.body_name)
    p_args = (body_node, cached.body_name, *new_lifted_args)
    flat_variable = add_call_function(
        tx,
        torch._higher_order_ops.invoke_subgraph,
        tuple(p_args),
        {},
        example_value,
        cached.config,
    )

    # Return only the user-visible outputs. The graph may have extra
    # intermediate outputs from side effects (allow_side_effects=True)
    # that should not be part of the user-facing return value.
    if cached.single_tensor_output:
        items = flat_variable.items  # pyrefly: ignore[missing-attribute]
        assert isinstance(items[0], TensorVariable), (
            f"Expected tensor output but got {type(items[0]).__name__}"
        )
        return items[0]

    items = flat_variable.items  # pyrefly: ignore[missing-attribute]
    n = cached.num_user_outputs
    if n > 0 and n < len(items):
        from .builder import SourcelessBuilder

        return SourcelessBuilder.create(tx, tuple(items[:n]))
    return flat_variable