def _call_function(
        self,
        tx: "InstructionTranslator",
        args: Sequence[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        args, kwargs = LazyVariableTracker.realize_all((args, kwargs))

        if len(kwargs) > 0:
            unimplemented(
                gb_type="torch.map: kwargs not supported",
                context=f"args: {args}, kwargs: {kwargs}",
                explanation=f"torch.map expects no keyword arguments (got {len(kwargs)})",
                hints=[
                    *graph_break_hints.USER_ERROR,
                ],
            )

        _check_supported_callable_arg(tx, args[0], "map_fn")

        # args = f, flat_xs, flat_args
        assert isinstance(args[1], (ListVariable, TupleVariable)), args[1]
        assert isinstance(args[2], (ListVariable, TupleVariable)), args[2]
        unpacked_xs = args[1].unpack_var_sequence(tx)
        unpacked_args = args[2].unpack_var_sequence(tx)

        sample_shape = get_fake_value(unpacked_xs[0].as_proxy().node, tx).size()

        if len(sample_shape) < 1 or sample_shape[0] == 0:
            unimplemented(
                gb_type="torch.map: improper inputs",
                context=str(sample_shape),
                explanation="torch.map doesn't support scalar or non-zero sized tensors during tracing.",
                hints=[
                    *graph_break_hints.USER_ERROR,
                ],
            )

        # To get the example output from map() we will need to provide at least one sample to
        # the loop body. In our case we will always use xs[0], and our map() won't support zero
        # sized tensor during tracing.
        with discard_graph_changes(tx):
            sliced_xs = [
                xs.call_method(
                    tx,
                    "select",
                    args=[VariableTracker.build(tx, 0), VariableTracker.build(tx, 0)],
                    kwargs={},
                )
                for xs in unpacked_xs
            ]
        assert self._HOP_NAME is not None

        # TODO: Support kwargs
        (
            (body_r, body_spec),
            body_graph,
            body_lifted_freevars,
        ) = speculate_subgraph(
            tx,
            args[0],
            [
                *sliced_xs,
                *unpacked_args,
            ],
            {},
            self._HOP_NAME,
            source_target=self.value,
            set_subgraph_inputs="flatten_manual",
            should_flatten_outputs=True,
            # TODO - removing consts from control flow ops need more work
            remove_consts_from_outputs=False,
            supports_input_mutation=self.supports_input_mutation,
            supports_aliasing=self.supports_aliasing,
        )

        # Check all outputs of map are tensors.
        # For map, outputting None is OK, thus ignore None values in the check
        body_r_vars = body_r.unpack_var_sequence(tx)
        none_mask = [x.is_constant_none() for x in body_r_vars]
        _check_all_tensorvariable(
            [br for bm, br in zip(none_mask, body_r_vars) if not bm]
        )

        body_nn_modules = dict(tx.output.nn_modules)

        body_name = tx.output.install_subgraph(
            "map_body",
            torch.fx.GraphModule(body_nn_modules, body_graph),
        )

        body_node = make_attr(tx, body_name)

        p_args = (
            body_node,
            [xs.as_proxy() for xs in unpacked_xs],
            [arg.as_proxy() for arg in unpacked_args]
            + list(body_lifted_freevars.keys()),
        )

        return _call_function_and_unflatten_output(
            tx, torch.ops.higher_order.map_impl, p_args, {}, None, body_spec, body_r
        )