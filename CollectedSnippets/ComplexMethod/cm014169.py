def _call_while_loop(
    self: Union[
        "WhileLoopHigherOrderVariable", "WhileLoopStackOutputHigherOrderVariable"
    ],
    tx: "InstructionTranslator",
    args: Sequence[VariableTracker],
    kwargs: dict[str, VariableTracker],
    stack_output: bool,
    hop_name: str,
) -> VariableTracker:
    from torch._higher_order_ops.while_loop import _create_unbacked_symint

    args, kwargs = LazyVariableTracker.realize_all((args, kwargs))
    cond_fn, body_fn, operands, additional_inputs = args

    # Input checks
    for i, k in enumerate(["cond_fn", "body_fn", "operands"]):
        if v := kwargs.pop(k, None):
            assert i == len(args), (
                "did not provide the right number of non-keyword args"
            )
            args.append(v)

    if kwargs or len(args) != 4:
        unimplemented(
            gb_type="torch.while_loop: improper args/kwargs",
            context=f"args: {args}, kwargs: {kwargs}",
            explanation=f"torch.while_loop expects 4 positional arguments (got {len(args)}) "
            f"and no keyword arguments (got {len(kwargs)}) "
            "Usage: while_loop(cond_fn, body_fn, operands)",
            hints=[
                *graph_break_hints.USER_ERROR,
            ],
        )

    # cond_fn and body_fn input check
    _check_supported_callable_arg(tx, cond_fn, "cond_fn")
    _check_supported_callable_arg(tx, body_fn, "body_fn")

    # operands input check
    operands_seq = operands.unpack_var_sequence(tx)

    # additional_inputs input check
    if not isinstance(additional_inputs, (ListVariable, TupleVariable)):
        unimplemented(
            gb_type="torch.while_loop: improper additional_inputs",
            context=str(additional_inputs),
            explanation=f"Expected additional_inputs to be a list/tuple but got {additional_inputs.python_type()}",
            hints=[
                *graph_break_hints.DYNAMO_BUG,
            ],
        )
    additional_inputs_seq = additional_inputs.unpack_var_sequence(tx)

    with discard_graph_changes(tx):
        # Note: this must be run under discard graph changes.
        def unspecialize_carried_inputs(
            tx: "InstructionTranslator", carry: VariableTracker
        ) -> VariableTracker:
            # See NOTE [unspecialize int carry with unbacked symints]
            if (
                carry.is_python_constant()
                and isinstance(carry.as_python_constant(), int)
            ) or isinstance(carry, SymNodeVariable):
                example_value = _create_unbacked_symint(
                    tx.output.fake_mode, ignore_fresh_unbacked_symbols=True
                )
                proxy = tx.output.current_tracer.create_graph_input(
                    "unbacked_symint", type(example_value), example_value
                )
                return SymNodeVariable.create(tx, proxy, example_value)
            else:
                # See NOTE [unspecialize constant tensor carry]
                assert carry.is_tensor()
                cloned_carry = carry.clone()
                # type: ignore[attr-defined]
                cloned_carry.proxy.node.meta["example_value"].constant = None
                return cloned_carry

        # clone inputs across subgraphs, to avoid unbacked memoization in fake prop
        cond_operands_seq = [
            unspecialize_carried_inputs(
                tx,
                (
                    carry.call_method(tx, "clone", args=(), kwargs={})
                    if carry.is_tensor()
                    else carry
                ),
            )
            for carry in operands_seq
        ]
        body_operands_seq = [
            unspecialize_carried_inputs(
                tx,
                (
                    carry.call_method(tx, "clone", args=(), kwargs={})
                    if carry.is_tensor()
                    else carry
                ),
            )
            for carry in operands_seq
        ]

    # create cond subgrpahs
    (
        (cond_r, _cond_treespec),
        cond_graph,
        cond_lifted_freevars,
    ) = speculate_subgraph(
        tx,
        cond_fn,
        cond_operands_seq + additional_inputs_seq,
        {},
        hop_name,
        source_target=self.value,
        # NOTE [why we cannot use "automatic" for while_loop]:
        # The reason is that we want to enforce
        # the ordering of inputs and outputs to be consistent and the ordering
        # of cond_fn and body_fn to the consistent.
        # e.g. suppose we use "automatic" and we have:
        #
        # def body_fn(ph1, ph2):
        #   new_a, new_b = ph2.cos(), ph1.sin()
        #   return new_a, new_b
        #
        # a, b = torch.randn(3), torch.randn(3)
        # new_a, new_b = body_fn(a, b)
        #
        # Using automatic, the ordering of arguments will be the order that they're
        # used. In this example, the capture graph looks like:
        #
        # def captured_body(ph1, ph2):
        #   new_a, new_b = ph1.cos(), ph2.add_(1)
        #   return new_a, new_b
        #
        # This is fine when we change the calling convention of captured_body to be
        # new_a, new_b = captured_body(b, a).
        # But for while_loop, the next iteration's input is previous iteration output
        # we'll end up feeding captured_body(new_a, new_b) instead.
        # So it's best we always enforce the ordering of carried_inputs the same as outputs
        # with "flatten_manual".
        set_subgraph_inputs="flatten_manual",
        supports_input_mutation=self.supports_input_mutation,
        supports_aliasing=self.supports_aliasing,
        remove_consts_from_outputs=False,
    )
    cond_nn_modules = dict(tx.output.nn_modules)
    validate_subgraph_output_types(cond_r)
    if cond_r.is_tensor():
        cond_r_meta = _extract_tensor_metadata(
            # type: ignore[attr-defined]
            cond_r.proxy.node.meta["example_value"],
            include_contiguity=False,
        )
        if cond_r_meta.dtype != torch.bool or cond_r_meta.shape != torch.Size([]):
            unimplemented(
                gb_type="torch.while_loop: unsupported cond_fn return type",
                context=str(cond_r),
                explanation=f"Expected cond_fn to return a scalar tensor or a bool but got {cond_r_meta.shape}.",
                hints=[
                    *graph_break_hints.USER_ERROR,
                ],
            )
    elif cond_r.is_python_constant():
        # short-circuiting while_loop when cond_fn returns a constant such as 0, 1 True or False
        pred = cond_r.as_python_constant()
        if pred:
            unimplemented(
                gb_type="torch.while_loop: infinite loop detected",
                context=str(cond_r),
                explanation=f"Infinite loop detected because while_loop's cond_fn always returns the same value {pred}.",
                hints=[
                    *graph_break_hints.USER_ERROR,
                ],
            )
        else:
            return operands

    # create body subgraph
    (
        (body_r, body_treespec),
        body_graph,
        body_lifted_freevars,
    ) = speculate_subgraph(
        tx,
        body_fn,
        body_operands_seq + additional_inputs_seq,
        {},
        hop_name,
        source_target=self.value,
        set_subgraph_inputs="flatten_manual",
        should_flatten_outputs=True,
        supports_input_mutation=False,
        supports_aliasing=False,
        remove_consts_from_outputs=False,
    )
    validate_subgraph_output_types(body_r)

    # We set include contiguity=False because we have vmap x HOP tests, where if
    # include_contiguity=True will call t.is_contiguous inside of vmap and get an error
    # "querying is_contiguous inside of vmap for memory_format other than
    # torch.contiguous_format is not yet implemented". This is okay because stride
    # is still checked.
    check_meta_consistency_vt(
        body_r.unpack_var_sequence(tx),
        operands_seq,
        "body_fn_output",
        "carried_inputs",
        include_contiguity=False,
    )

    (
        cond_graph,
        body_graph,
        cond_shared,
        _body_shared,
        cond_unique,
        body_unique,
    ) = _merge_graph_inputs(
        cond_graph,
        cond_lifted_freevars,
        "cond_fn",
        body_graph,
        body_lifted_freevars,
        "body_fn",
    )

    # Note: cond_shared and body_shared refer to the same proxy in parent graph
    # so using either of them is OK. Use cond_shared as it doesn't matter.
    additional_lifted_inputs = cond_shared + cond_unique + body_unique

    body_nn_modules = dict(tx.output.nn_modules)

    cond_gm = torch.fx.GraphModule(cond_nn_modules, cond_graph)
    body_gm = torch.fx.GraphModule(body_nn_modules, body_graph)
    cond_name = tx.output.install_subgraph("cond_fn", cond_gm)
    body_name = tx.output.install_subgraph("body_fn", body_gm)

    cond_node = make_attr(tx, cond_name)
    body_node = make_attr(tx, body_name)

    operands_proxy = tuple(operand.as_proxy() for operand in operands_seq)
    additional_inputs_proxy = tuple(
        [inp.as_proxy() for inp in additional_inputs_seq] + additional_lifted_inputs
    )
    p_args = (
        cond_node,
        body_node,
        operands_proxy,
        additional_inputs_proxy,
    )
    return _call_function_and_unflatten_output(
        tx,
        self.value,
        p_args,
        {},
        None,
        body_treespec,
        body_r,
    )