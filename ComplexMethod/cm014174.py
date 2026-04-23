def speculate_subgraph(
    tx: "InstructionTranslator",
    f: VariableTracker,
    sub_args: Sequence[VariableTracker],
    sub_kwargs: dict[str, VariableTracker] | None,
    description: str,
    *,
    # source_target is the .value of HigherOrderOpVariable and is the
    # target of the proxy that we created for the higherOrderOperator.
    source_target: HigherOrderOperator | None = None,
    always_restore: bool = False,
    enable_grad: bool | None = None,
    # NOTE [argument `set_subgraph_inputs`]
    # set_subgraph_inputs controls what how to construct subgraphs' placeholders from sub_args.
    # 1. if your HOP supports arbitrary inputs, use set_subgraph_inputs="automatic" (most recommended).
    # 2. if your HOP supports only Tensor and symnode inputs, use set_subgraph_inputs="flatten_manual" (recommended).
    # If sub_args contain Pytree structure (e.g. dict/list/tuple/set), the sub_args will be flattened first.
    # Then the flattened args are manually set as subgraph's placeholders.
    # 3. if your HOP must preserve inputs that are not tensor or symnode as placeholders e.g. AutogradFunctionContextVariable
    # use set_subgraph_inputs="manual" (not recommended). We do not recommend it in general because it has the
    # restriction that user need to manually control how to create placeholders and VariableTrackers for the args.
    set_subgraph_inputs: Literal[
        "automatic", "semi_automatic", "flatten_manual", "manual"
    ] = "automatic",
    restore_side_effects: bool = True,
    should_flatten_outputs: bool = False,
    # if should_flatten_outputs is True, `remove_consts_from_outputs` remove the
    # const outputs from the subgraph output.
    remove_consts_from_outputs: bool = True,
    # TODO - supports input_mutation and aliasing should be False by default for strictness
    supports_input_mutation: bool = True,
    supports_aliasing: bool = True,
    # Pass in an originating tracer - this is needed for preserving context
    # across fwd-bwd for autograd.Function
    tracer: Optional["SubgraphTracer"] = None,
) -> tuple[tuple[VariableTracker, OutputSpec], torch.fx.Graph, dict[Proxy, Proxy]]:
    if sub_kwargs is None:
        sub_kwargs = {}

    from .builder import SourcelessBuilder

    assert set_subgraph_inputs in {
        "automatic",
        "automatic_with_forced_inputs",
        "flatten_manual",
        "manual",
    }, "Please use one of the supported set_subgraph_inputs options."

    # See NOTE [Temporary argument `set_subgraph_inputs`]
    if sub_kwargs and set_subgraph_inputs != "automatic":
        unimplemented(
            gb_type="invalid set_subgraph_inputs and sub_kwargs settings",
            context=f"set_subgraph_inputs: {set_subgraph_inputs}, sub_kwargs: {sub_kwargs}",
            explanation="`sub_kwargs` cannot be used when `set_subgraph_inputs` is not set to 'automatic'.",
            hints=[
                "Use `set_subgraph_inputs='automatic'` when passing `sub_kwargs`.",
                *graph_break_hints.USER_ERROR,
            ],
        )

    try:
        # ensure guards on args get installed in parent subgraph
        f, sub_args, sub_kwargs = LazyVariableTracker.realize_all(
            (f, sub_args, sub_kwargs),
        )

        with tx.output.subtracer(source_target, tracer, description) as subtracer:
            args = get_hop_args(
                tx, f, subtracer, sub_args, sub_kwargs, set_subgraph_inputs, description
            )

            output = trace_hop_function(
                f,
                tx,
                subtracer,
                enable_grad,
                restore_side_effects,
                args,
                sub_kwargs,
            )

            treespec = None
            masks_to_filter_const_values = None
            const_values = None
            if should_flatten_outputs:
                from torch._dynamo.external_utils import filter_out_const_values

                # Flatten the speculated subgraph output.
                output, treespec = _make_inlined(tx, pytree.tree_flatten)(
                    output
                ).unpack_var_sequence(tx)

                # Actually, transform the list (returned by flatten) into a tuple
                # for dynamo consistency.
                output = SourcelessBuilder.create(tx, tuple).call_function(
                    tx, [output], {}
                )

                if remove_consts_from_outputs:
                    # Filter out the constants and save them into a spec. Filtering
                    # out constants makes the graph simpler for the backends. We
                    # need to ensure that after unflattening the constants are
                    # inserted back at the right positions for the Dynamo tracing to
                    # continue. This is done by filter_const_spec
                    output_proxies = output.as_proxy()
                    masks_to_filter_const_values = pytree.tree_map(
                        lambda x: not isinstance(x, torch.fx.Proxy), output_proxies
                    )
                    const_values = pytree.tree_map(
                        lambda x: None if isinstance(x, torch.fx.Proxy) else x,
                        output_proxies,
                    )
                    output = _make_inlined(tx, filter_out_const_values)(
                        output, masks_to_filter_const_values
                    )

            # TODO - clean up num_intermediate_nodes_as_outputs - we do not need
            # after AC moved to auto_output_flattening
            num_intermediate_nodes_as_outputs = 0
            # Register output to graph
            # Modeled off of compile_and_call_fx_graph
            # TODO: support pytree output
            # We check always_restore because we dont use the output or side effects of always_restore code,
            # like bwd.
            if always_restore:
                # Nothing left to do here
                return (
                    (
                        output,
                        OutputSpec(
                            treespec,  # type: ignore[arg-type]
                            masks_to_filter_const_values,
                            const_values,
                            num_intermediate_nodes_as_outputs,
                        ),
                    ),
                    tx.output.graph,
                    subtracer.lifted_freevars,
                )
            else:
                validate_subgraph_output_types(output)

                # The output proxies might not belong to this SubgraphTracer
                # (if they are free variables that were never lifted)
                # so lift them here.
                output_proxies = output.as_proxy()
                output_proxies = pytree.tree_map(
                    subtracer.maybe_lift_tracked_freevar_to_input, output_proxies
                )

                tx.output.create_node(
                    "output",
                    "output",
                    (subtracer.create_arg((output_proxies,))),
                    {},
                )
                graph = tx.output.graph
                graph.lint()
                lifted_freevars = subtracer.lifted_freevars

                if len(lifted_freevars) > 0:
                    move_lifted_freevars_phs_to_end(graph, lifted_freevars)
                check_aliasing_and_input_mutation(
                    subtracer,
                    graph,
                    supports_input_mutation,
                    supports_aliasing,
                    source_target,
                )

                return (
                    (
                        output,
                        OutputSpec(
                            treespec,  # type: ignore[arg-type]
                            masks_to_filter_const_values,
                            const_values,
                            num_intermediate_nodes_as_outputs,
                        ),
                    ),
                    graph,
                    lifted_freevars,
                )

    except Unsupported as ex:
        f_name = f"{type(f).__name__}"
        if isinstance(f, UserFunctionVariable):
            f_name = f.get_name()
        msg = (
            f"speculate_subgraph: while introspecting {description}, we were unable "
            f"to trace function `{f_name}` into a single graph. This means "
            f"that Dynamo was unable to prove safety for this API and will "
            f"fall back to eager-mode PyTorch, which could lead to a slowdown."
        )
        log.info(msg)
        log.info(ex)
        raise ex