def call_function(
        self,
        tx: "InstructionTranslator",
        args: Sequence[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        args, kwargs = LazyVariableTracker.realize_all((args, kwargs))

        if kwargs:
            unimplemented(
                gb_type="wrap_with_autocast: unexpected kwargs",
                context=f"args: {args}, kwargs: {kwargs}",
                explanation=f"wrap_with_autocast expects no keyword arguments (got {len(kwargs)}).",
                hints=[
                    *graph_break_hints.DYNAMO_BUG,
                ],
            )

        device_type, dtype, enabled, cache_enabled, fn_var, *rest_args = args

        for arg in [device_type, dtype, enabled, cache_enabled]:
            if not arg.is_python_constant():
                unimplemented(
                    gb_type="wrap_with_autocast: expected constant arg",
                    context=str(args),
                    explanation="wrap_with_autocast expects device_type, dtype, enabled, "
                    "and cache_enabled arguments to be constants.",
                    hints=[
                        *graph_break_hints.DYNAMO_BUG,
                    ],
                )

        _check_supported_callable_arg(tx, fn_var, "autocast")

        python_constants = [
            arg.as_python_constant()
            for arg in [device_type, dtype, enabled, cache_enabled]
        ]

        with torch.autocast(*python_constants):
            assert self._HOP_NAME is not None
            (
                (body_r, treespec),
                body_graph,
                body_lifted_freevars,
            ) = speculate_subgraph(
                tx,
                fn_var,
                [*rest_args],
                {},
                self._HOP_NAME,
                source_target=self.value,
                set_subgraph_inputs="manual",
                should_flatten_outputs=True,
            )

        if len(body_lifted_freevars) > 0:
            unimplemented(
                gb_type="wrap_with_autocast: unexpected freevars",
                context=str(body_lifted_freevars),
                explanation="wrap_with_autocast expects no freevars.",
                hints=[],
            )

        body_gmod = torch.fx.GraphModule(tx.output.nn_modules, body_graph)
        body_name = tx.output.install_subgraph(
            "wrap_body",
            body_gmod,
        )

        body_node = make_attr(tx, body_name)

        proxy_args = tuple(
            [
                *python_constants,
                body_node,
            ]
            + [operand.as_proxy() for operand in rest_args]
        )
        example_value = pytree.tree_map_only(
            torch.fx.Proxy,
            lambda a: a.node.meta["example_value"],
            body_r.as_proxy(),
        )

        return _call_function_and_unflatten_output(
            tx, self.value, proxy_args, {}, example_value, treespec, body_r
        )