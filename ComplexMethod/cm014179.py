def _call_function(
        self,
        tx: "InstructionTranslator",
        args: Sequence[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        from torch._higher_order_ops.utils import first_slice_copy

        args, kwargs = LazyVariableTracker.realize_all((args, kwargs))

        def arg_extractor(
            combine_fn: VariableTracker,
            xs: VariableTracker,
            additional_inputs: VariableTracker,
        ) -> tuple[VariableTracker, VariableTracker, VariableTracker]:
            return combine_fn, xs, additional_inputs

        combine_fn, xs, additional_inputs = arg_extractor(*args, **kwargs)

        if args[0].python_type() is functools.partial:
            # This is the standard case when the user calls the frontend
            # and the frontend invokes dynamo
            if len(args) != 2:
                unimplemented(
                    gb_type="torch.associative_scan: improper args",
                    context=f"args: {args}",
                    explanation=f"torch.associative_scan expects 2 positional arguments (got {len(args)}) "
                    "Usage: associative_scan(combine_fn, xs)",
                    hints=[
                        *graph_break_hints.USER_ERROR,
                    ],
                )

            xs_treespec = args[0].keywords["spec"]

            # combine_fn input check
            # We need to get the pure combine_fn from the functools.partial
            _check_supported_callable_arg(
                tx,
                combine_fn.keywords["combine_fn"],  # type: ignore[attr-defined]
                "combine_fn",
            )
        else:
            # This case is hit during re-tracing, for example in export tests
            # In this case, the combine_fn is a callable and not a functools.partial
            xs_treespec = _make_inlined(tx, pytree.tree_structure)(xs)

            _check_supported_callable_arg(tx, combine_fn, "combine_fn")

        # xs input check
        if not isinstance(xs, (ListVariable, TupleVariable)):
            unimplemented(
                gb_type="torch.associative_scan: improper xs",
                context=str(xs),
                explanation=f"Expected xs to be a list/tuple but got {xs.python_type()}",
                hints=[
                    *graph_break_hints.DYNAMO_BUG,
                ],
            )
        xs_vars = xs.unpack_var_sequence(tx)
        _check_all_tensorvariable(xs_vars)

        # additional_inputs input check
        if not isinstance(additional_inputs, (ListVariable, TupleVariable)):
            unimplemented(
                gb_type="torch.associative_scan: improper additional_inputs",
                context=str(additional_inputs),
                explanation=f"Expected additional_inputs to be a list/tuple but got {additional_inputs.python_type()}",
                hints=[
                    *graph_break_hints.DYNAMO_BUG,
                ],
            )
        additional_inputs_vars = additional_inputs.unpack_var_sequence(tx)
        _check_all_tensorvariable(additional_inputs_vars)

        scan_length = get_fake_value(xs_vars[0].as_proxy().node, tx).size()[0]
        if scan_length == 0:
            unimplemented(
                gb_type="torch.associative_scan: zero-sized tensor",
                context=str(xs_vars[0]),
                explanation="associative_scan() operator doesn't support zero-sized tensors during tracing.",
                hints=[
                    *graph_break_hints.USER_ERROR,
                ],
            )

        # Trace the subgraph
        # The sub_args is a slice of original input, e.g. if input.size is (3, 4), and scan dim=0
        # the sub_args shape will be (4, ).
        with discard_graph_changes(tx):
            sub_args = [
                _make_inlined(tx, first_slice_copy)(leaf)
                for leaf in itertools.chain(xs_vars, xs_vars)
            ]
            sub_args_additional_inputs = [
                t.call_method(tx, "clone", args=[], kwargs={})
                for t in additional_inputs_vars
            ]

        sub_args = sub_args + sub_args_additional_inputs
        assert self._HOP_NAME is not None
        (
            (combine_result, _combine_spec),
            combine_graph,
            combine_lifted_freevars,
        ) = speculate_subgraph(
            tx,
            combine_fn,
            sub_args,
            sub_kwargs={},
            description=self._HOP_NAME,
            source_target=self.value,
            set_subgraph_inputs="flatten_manual",
            supports_input_mutation=self.supports_input_mutation,
            supports_aliasing=self.supports_aliasing,
        )

        # Ensure that the output of scan is a flattened list of elements,
        # because downstream operations assume that the output of HOPs
        # is flattened
        output_node = combine_graph.find_nodes(op="output")[0]
        output_node.args = (pytree.tree_leaves(output_node.args),)
        combine_graph.lint()

        # Collect the results from the combine_fn
        results, _combine_treespec = _make_inlined(tx, pytree.tree_flatten)(
            combine_result
        ).unpack_var_sequence(tx)

        # Check whether the combine_fn returns one child tree for the output.
        if _combine_treespec.as_python_constant().num_leaves < 1:
            unimplemented(
                gb_type="torch.associative_scan: combine_fn improper number of leaves",
                context=str(_combine_treespec.as_python_constant()),
                explanation="combine_fn needs to produce one pytree for the output "
                f"but combine_fn produces the pytree {_combine_treespec.as_python_constant()}.",
                hints=[
                    *graph_break_hints.USER_ERROR,
                ],
            )

        # Check whether the outs produced by combine_fn has the same treespec as xs
        # We need to have this check this way, because in case init is a TreeSpec and carry
        # but carry is only a LeafSpec, these two cannot be compared correctly.
        if (
            xs_treespec.as_python_constant().is_leaf()
            != _combine_treespec.as_python_constant().is_leaf()
        ) or not _make_inlined(tx, pytree.TreeSpec.__eq__)(
            xs_treespec, _combine_treespec
        ).as_python_constant():
            unimplemented(
                gb_type="torch.associative_scan: mismatched input/output tree structure",
                context=f"xs: {xs_treespec.as_python_constant()}, output: {_combine_treespec.as_python_constant()}",
                explanation="The tree structure of the xs and the outs of the combine_fn are are expected to be identical, but got "
                f"xs: {xs_treespec.as_python_constant()} vs output: {_combine_treespec.as_python_constant()}.",
                hints=[
                    *graph_break_hints.USER_ERROR,
                ],
            )

        # We set include contiguity=False because we have vmap x HOP tests, where if
        # include_contiguity=True will call t.is_contiguous inside of vmap and get an error
        # "querying is_contiguous inside of vmap for memory_format other than
        # torch.contiguous_format is not yet implemented". This is okay because stride
        # is still checked.
        check_meta_consistency_vt(
            [_make_inlined(tx, first_slice_copy)(t) for t in xs_vars],
            results.items,  # type: ignore[attr-defined]
            "initial_xs",
            "combine_fn_output",
            include_contiguity=False,
        )

        combine_gm = torch.fx.GraphModule(dict(tx.output.nn_modules), combine_graph)
        combine_freevars_proxy = tuple(combine_lifted_freevars.keys())

        # Compute the proxies for the input check
        proxy_vars_inputcheck = (
            tuple(sarg.as_proxy() for sarg in sub_args) + combine_freevars_proxy
        )

        from torch._higher_order_ops.utils import _maybe_fake_tracing
        from torch._inductor.utils import is_pointwise_use

        assert tx.fake_mode is not None
        with tx.fake_mode:
            sub_args_fake = [
                (
                    leaf.node.meta["example_value"].clone()
                    if hasattr(leaf.node.meta["example_value"], "clone")
                    else leaf.node.meta["example_value"]
                )
                for leaf in pytree.tree_leaves(proxy_vars_inputcheck)
            ]
            pre_dispatch = False

            fx = _maybe_fake_tracing(
                combine_gm, sub_args_fake, pre_dispatch=pre_dispatch
            )

            for node in fx.graph.nodes:
                # Check that the combine_fn is pointwise, if combine_mode='pointwise'
                if not all(
                    is_pointwise_use(use) or use.op == "output" for use in node.users
                ):
                    raise RuntimeError(
                        "For combine_mode='pointwise', the combine_fn needs to be pointwise"
                    )

        combine_fn_name = tx.output.install_subgraph(
            "associative_scan_combine_fn", combine_gm
        )

        # Compute the proxies
        xs_proxy = xs.as_proxy()
        combine_freevars_proxy = tuple(combine_lifted_freevars.keys())
        additional_inputs_proxy = additional_inputs.as_proxy() + combine_freevars_proxy

        p_args = (
            make_attr(tx, combine_fn_name),
            xs_proxy,
            additional_inputs_proxy,
        )

        return _call_function_and_unflatten_output(
            tx,
            torch.ops.higher_order.associative_scan,
            p_args,
            {},
            None,
            OutputSpec(xs_treespec),  # type: ignore[arg-type]
            None,
        )