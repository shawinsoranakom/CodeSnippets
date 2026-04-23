def validate_args_and_maybe_create_graph_inputs(
    sub_args: list[VariableTracker],
    tracer: "SubgraphTracer",
    tx: "InstructionTranslator",
    set_subgraph_inputs: str,
    description: str,
    sub_args_names: Sequence[str] | None = None,
) -> list[Any]:
    from . import AutogradFunctionContextVariable
    from .builder import SourcelessBuilder, wrap_fx_proxy_cls

    assert tracer.parent is not None

    if set_subgraph_inputs == "flatten_manual":
        flat_args, tree_spec = _make_inlined(tx, pytree.tree_flatten)(
            SourcelessBuilder.create(tx, sub_args)
        ).unpack_var_sequence(tx)

        flat_inputs = validate_args_and_maybe_create_graph_inputs(
            flat_args.unpack_var_sequence(tx),
            tracer,
            tx,
            set_subgraph_inputs="manual",
            description=description,
        )

        return _make_inlined(tx, pytree.tree_unflatten)(
            SourcelessBuilder.create(tx, list(flat_inputs)), tree_spec
        ).unpack_var_sequence(tx)
    else:
        if sub_args_names is not None:
            # Can be greater if user passes some args as kwargs
            assert len(sub_args_names) >= len(sub_args)
        args = []
        for idx, a in enumerate(sub_args):
            assert isinstance(a, VariableTracker)
            new_arg = None
            if set_subgraph_inputs == "automatic":
                args.append(a)
                continue
            elif set_subgraph_inputs == "automatic_with_forced_inputs":
                if isinstance(a, variables.TensorVariable):
                    node = a.maybe_fx_node()
                    assert node is not None
                    example_value = node.meta["example_value"]
                    arg_name = (
                        a.as_proxy().node.name
                        if sub_args_names is None
                        else sub_args_names[idx]
                    )
                    new_proxy = tracer.create_graph_input(
                        arg_name, a.python_type(), example_value
                    )
                    example_value = node.meta.get("example_value", None)
                    a = wrap_fx_proxy_cls(
                        target_cls=type(a),
                        tx=tx,
                        proxy=new_proxy,
                        example_value=example_value,
                    )
                args.append(a)
                continue

            if a.is_python_constant():
                # This arg is not used in the body of the higher order op.
                # Currently, this new input is added to make the calls
                # happy, which expect a fixed number of arguments. In
                # future, we can clean this up.
                arg_name = (
                    "const_unused"
                    if sub_args_names is None
                    else f"const_unused_{sub_args_names[idx]}"
                )
                tracer.create_graph_input(
                    arg_name, a.python_type(), a.as_python_constant()
                )
                new_arg = a
            # Weird special case, we probably want to delete it or fold it
            # into the next case (of `a` being placeable into a graph)
            elif isinstance(a, AutogradFunctionContextVariable):
                example_value = a.as_proxy().node.meta["example_value"]
                arg_name = (
                    a.as_proxy().node.name
                    if sub_args_names is None
                    else sub_args_names[idx]
                )
                tracer.create_graph_input(arg_name, a.python_type(), example_value)
                new_arg = a
            # If `a` can be put into a graph
            elif a.maybe_fx_node() is not None:
                node = a.maybe_fx_node()
                assert node is not None
                example_value = node.meta.get("example_value", None)
                arg_name = node.name if sub_args_names is None else sub_args_names[idx]
                new_proxy = tracer.create_graph_input(
                    arg_name, a.python_type(), example_value
                )
                new_arg = wrap_fx_proxy_cls(
                    target_cls=type(a),
                    tx=tx,
                    proxy=new_proxy,
                    example_value=example_value,
                )
            # If `a` cannot be put into a graph
            else:
                # HOPs work much better if they use speculate_subgraph(set_subgraph_inputs="automatic").
                unimplemented(
                    gb_type="HOP body taking non-Tensor as input",
                    context=str(sub_args),
                    explanation=f"{description} with body that accepts non-Tensors as input. "
                    f"Got type {a.python_type()} at index {idx}.",
                    hints=[
                        *graph_break_hints.USER_ERROR,
                    ],
                )
            args.append(new_arg)
        return args