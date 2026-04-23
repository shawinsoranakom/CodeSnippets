def speculate_subgraph_with_auto_output_flattening(
    tx: "InstructionTranslator",
    f: VariableTracker,
    sub_args: Sequence[VariableTracker],
    sub_kwargs: dict[str, VariableTracker] | None,
    description: str,
    *,
    # source_target is the .value of HigherOrderOpVariable and is the
    # target of the proxy that we created for the higherOrderOperator.
    source_target: HigherOrderOperator | None = None,
    enable_grad: bool | None = None,
    # automatic: relies on Dynamo to find the used tensors and lift them as
    # inputs.
    #
    # automatic_with_forced_inputs: relies on the function arg names to create
    # a new proxy. Also, it will always INSERT a tensor placeholder as input,
    # even though it might not be used in the graph and they will also be in the
    # same order as the original function (as opposed to automatic which will
    # not insert the unused placeholder and can insert other placeholders in the
    # order they are see while tracing). This is useful for autograd.Function
    # backward where we do need to account for all the inputs of the backwards
    # to be lifted as inputs for making the fwd-bwd graph consistent.
    set_subgraph_inputs: Literal[
        "automatic", "automatic_with_forced_inputs", "flatten_manual", "manual"
    ] = "automatic",
    # If True, exposes intermediates to subgraph outputs to allow later tensor ops to
    # access intermediates from the subgraph, this is useful for mutation
    allow_side_effects: bool = False,
    # Controls whether to filter aliased intermediates when collecting extra outputs.
    # This is only relevant when allow_side_effects=True.
    # - True: Filter out intermediates that alias with inputs or outputs (strict, for invoke_subgraph)
    # - False: Allow aliased intermediates (for checkpoint/autograd.Function which get desugared/inlined)
    #
    # Example where filtering is needed:
    #
    #   @invoke_subgraph
    #   def gn(x):
    #       view = x.view(2, 4)  # intermediate that aliases input x
    #       y = torch.sin(view)
    #       return torch.cos(view)
    #
    #   def fn(x):
    #       res = gn(x)
    #       return res + 4
    #
    # In this case, if we don't filter `view`, we would later error because some HOPs
    # have strict aliasing checks on inputs/outputs.
    #
    # This does however introduce a subtle issue when we do something like:
    #
    #   captured = []
    #
    #   @invoke_subgraph
    #   def gn(x):
    #       view = x.view(2, 4)  # intermediate that aliases input x
    #       y = torch.sin(view)
    #       captured.append(view)
    #       return torch.cos(view)
    #
    #   def fn(x):
    #       res = gn(x)
    #       return res + captured[0]
    #
    # In this case, we will not replay the side effect on `captured` in the graph,
    # which fails with a not-so-nice error. We will address this in a follow-up PR
    # because this case is rare. This is not a regression because side effects were
    # never supported for invoke_subgraph anyway.
    filter_aliased_intermediates: bool = False,
    # TODO - supports input_mutation and aliasing should be False by default for strictness
    supports_input_mutation: bool = True,
    supports_aliasing: bool = True,
    # Pass in an originating tracer - this is needed for preserving context
    # across fwd-bwd for autograd.Function
    tracer: Optional["SubgraphTracer"] = None,
) -> tuple[
    VariableTracker,  # output: The VT that Dynamo continues tracing with
    torch.fx.Graph,  # graph: The FX graph representing the subgraph computation
    dict[
        torch.fx.Proxy, torch.fx.Proxy
    ],  # lifted_freevars: Free variables lifted as inputs
    VariableTracker
    | tuple[
        VariableTracker, ...
    ],  # graph_output_vts: Tensor/symint VTs that are actual FX graph outputs
    SubgraphTracingInfo,  # tracing_info: Properties observed during subgraph tracing
]:
    """
    Speculate subgraph for Higher-Order Operators (HOPs) with automatic output flattening.

    ## Automatic output flattening

    For many HOPs, the representation exists only as a container for the
    subgraph. In later compiler stages or at runtime, the HOP is desugared and
    simply executes the subgraph directly, as if it were inlined. For such hops,
    we follow automatic output flattening.
    For example:
    - invoke_subgraph
    - activation checkpointing (torch.utils.checkpoint.checkpoint)
    - autograd.Function
    - nested_compile_region

    This is in contrast to control flow HOPs which do not follow this desugaring:
    - torch.cond (conditional execution based on predicate)
    - torch.while_loop (iterative execution)
    - torch.map (parallel execution over batch dimension)

    For control flow HOPs, the HOP behavior is fundamentally different from just
    running the body function once.

    ## Key Advantage: Disentangling VTs from Graph Outputs

    Desugaring simplify HOP processing by allowing us to disentangle the output
    variable trackers (VTs) from the HOP subgraph outputs. This mirrors typical
    Dynamo processing where:
    - VTs "run ahead" representing the program state for continued tracing
    - The graph is a side data structure tracking computation seen so far

    This separation is crucial for HOPs with non-proxyable outputs (e.g., custom
    user-defined objects containing tensors). The function may return complex Python
    objects for Dynamo to continue tracing, but only the tensor/symint VTs need to
    be registered as actual FX graph outputs.

    Example:
        class Foo:
            def __init__(self, a, b):
                self.a = a  # tensor
                self.b = b  # tensor

        def gn(x):
            return Foo(torch.sin(x), torch.cos(x))

        result = some_hop(gn, x)  # Returns Foo instance
        out = result.a + result.b  # Dynamo can continue tracing

    Here, `output` VT is a UserDefinedObjectVariable wrapping Foo, but
    `graph_output_vts` contains only the tensor VTs (a and b) that should be
    actual FX graph outputs. This allows Dynamo to continue tracing with the
    Foo object while the graph only needs to output the constituent tensors.

    ## Return Values

    Unlike `speculate_subgraph`, this function returns:
    - output: The VT that Dynamo continues tracing with (may be complex Python objects)
    - graph: The FX graph representing the subgraph computation
    - lifted_freevars: Free variables lifted as inputs to the subgraph
    - graph_output_vts: Only the tensor/symint VTs that are actual FX graph outputs

    The key difference is `graph_output_vts` instead of `treespec`, which gives more
    flexibility for handling non-proxyable outputs.
    """
    if sub_kwargs is None:
        sub_kwargs = {}

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
        with tx.output.subtracer(source_target, tracer, description) as subtracer:
            args = get_hop_args(
                tx,
                f,
                subtracer,
                list(sub_args),
                sub_kwargs,
                set_subgraph_inputs,
                description,
            )

            # Special case - if users uses
            # `traced_with_externally_visible_side_effects`, we still need to
            # return the intermediates as outputs. However, this API gets
            # triggered during the hop tracing,  and we don't know at this point
            # of time, if the API will take into effect. To handle this, we have
            # a flag traced_with_externally_visible_side_effects (default=False)
            # that is set to True anytime
            # `traced_with_externally_visible_side_effects` is set. We reset it
            # with the old value after the hop is traced out.
            old_value = (
                tx.output.current_tracer.traced_with_externally_visible_side_effects
            )

            output = trace_hop_function_with_auto_output_flattening(
                f,
                tx,
                subtracer,
                enable_grad,
                allow_side_effects,
                args,
                sub_kwargs,
            )

            # NOTE: [Separation of graph outputs and output VTs]
            # In Dynamo (outside of speculate_subgraph), VTs and the graph are
            # separate concepts:
            # - VTs (VariableTrackers) can "run ahead" and continue Dynamo tracing
            # - The graph is just a side data structure tracking computation seen so far
            #
            # This separation is crucial for HOPs with non-proxyable outputs (e.g.,
            # custom user-defined objects containing tensors). The function may return
            # complex Python objects for Dynamo to continue tracing, but only the
            # tensor/symint VTs need to be registered as actual graph outputs.
            #
            # Example:
            #   class Foo:
            #       def __init__(self, a, b):
            #           self.a = a  # tensor
            #           self.b = b  # tensor
            #
            #   def gn(x):
            #       return Foo(torch.sin(x), torch.cos(x))
            #
            # Here, `output` VT is a UserDefinedObjectVariable wrapping Foo, but
            # `graph_output_vts` contains only the tensor VTs (a and b) that should
            # be actual FX graph outputs.
            # Collect only tensor and symint VTs that should be graph outputs.
            # We walk the output structure and extract proxyable VTs.
            graph_output_vt_list = []

            def visit(vt: VariableTracker) -> None:
                if vt.is_tensor() or isinstance(
                    vt, (SymNodeVariable, TorchScriptObjectVariable)
                ):
                    graph_output_vt_list.append(vt)

            VariableTracker.visit(visit, output, side_effects=tx.output.side_effects)
            graph_output_vts = tuple(graph_output_vt_list)

            # NOTE - [Return subgraph intermediates as subgraph outputs]
            # This helps HOPs which allow side effects. Consider the
            # following example
            #
            # def gn(x, z):
            #     o = torch.matmul(x, x) @ x
            #     out = x.sin()
            #     z.append(out)
            #     return torch.cos(torch.sin(o))

            # def fn(x):
            #     z = []
            #     out1 = torch.utils.checkpoint.checkpoint(
            #         gn,
            #         x,
            #         z,
            #         use_reentrant=False,
            #     )
            #     return out1, z[0]
            #
            # In this example, list `z` is in outer scope and gets appended
            # in the subgraph with `out`. But `out` is not an output of the
            # subgraph. This can cause issue because later on when the outer
            # graph returns `z[0]` it needs to have access to the graph node
            # `out`. To solve this problem, we just return all intermediates
            # from the subgraph.

            # TODO - Today this is supported only for AC. AC HOP gets
            # desugared in AOTDispatcher so even though subgraph has extra
            # unused outputs in Dynamo, its ok even if we don't DCE them in
            # Dynamo. As AOTDispatcher desugars/inlines the subgraph, the
            # subgraph boundary disappears. And even for AC, today this only
            # works when the skip_fwd_side_effects_in_bwd_under_checkpoint
            # flag is True, i.e., only when we allow side-effects. But, we
            # want this to be supported for other Hops as well, specifically
            # nested_compile_region and autograd.Function. Today, its safe
            # because we error out on seeing a side-effect.

            traced_externally = (
                tx.output.current_tracer.traced_with_externally_visible_side_effects
            )
            has_side_effects = (
                subtracer.side_effect_stack is not None or traced_externally
            )
            if (allow_side_effects or traced_externally) and has_side_effects:
                extra_outputs = collect_intermediate_outputs(
                    tx, subtracer, graph_output_vts, filter_aliased_intermediates
                )
                graph_output_vts = graph_output_vts + tuple(extra_outputs)

            tx.output.current_tracer.traced_with_externally_visible_side_effects = (
                old_value
            )

            validate_subgraph_output_types(graph_output_vts)

            # The output proxies might not belong to this SubgraphTracer
            # (if they are free variables that were never lifted)
            # so lift them here.
            # output_proxies = output.as_proxy()
            if isinstance(graph_output_vts, tuple):
                output_proxies = [a.as_proxy() for a in graph_output_vts]  # type: ignore[attr-defined]
                output_proxies = pytree.tree_map(
                    subtracer.maybe_lift_tracked_freevar_to_input, output_proxies
                )
                output_proxies = tuple(output_proxies)
            else:
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
            # Return both the output VT and the graph output VTs separately:
            # - `output`: The VT that Dynamo continues tracing with (may be
            #   complex Python objects, tuples, dicts, etc.)
            # - `graph`: The FX graph representing the subgraph computation
            # - `lifted_freevars`: Free variables lifted as inputs to the subgraph
            # - `graph_output_vts`: Only the tensor/symint VTs that are actual
            #   FX graph outputs (basically the vts associated with graph outputs)
            # - `tracing_info`: Properties observed during subgraph tracing
            tracing_info = SubgraphTracingInfo(
                side_effect_stack=subtracer.side_effect_stack,
                traced_sources=subtracer.traced_sources,
            )

            return (
                output,
                graph,
                lifted_freevars,
                graph_output_vts,
                tracing_info,
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