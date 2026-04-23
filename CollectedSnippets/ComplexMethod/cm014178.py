def _call_function(
        self,
        tx: "InstructionTranslator",
        args: Sequence[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        from . import ListVariable

        self.supports_input_mutation = not torch.is_grad_enabled()
        self.supports_aliasing = not torch.is_grad_enabled()

        args, kwargs = LazyVariableTracker.realize_all((args, kwargs))

        for i, k in enumerate(["pred", "true_fn", "false_fn", "operands"]):
            if v := kwargs.pop(k, None):
                assert i == len(args), (
                    "did not provide the right number of non-keyword args"
                )
                args.append(v)

        # TODO(voz): Support fake tensor dispatch for recursive
        # ops - see torch/dispatch/_dispatcher.py
        if len(args) != 4 or kwargs:
            unimplemented(
                gb_type="torch.cond: improper args/kwargs",
                context=f"args: {args}, kwargs: {kwargs}",
                explanation=f"torch.cond expects 4 positional arguments (got {len(args)}) "
                f"and no keyword arguments (got {len(kwargs)}) "
                "Usage: cond(pred, cond_fn, body_fn, operands)",
                hints=[
                    *graph_break_hints.USER_ERROR,
                ],
            )

        # Specialize into one of the branches since pred is constant
        pred, true_fn, false_fn, operands = args
        if type(args[0]) is ConstantVariable:
            warnings.warn(
                "Pred is a Python constant. When used with torch.cond, it specializes on one of the branches."
                " If you want torch.cond to preserve two branches, please make the predicate a boolean tensor or a SymBool.",
                UserWarning,
            )
            if pred.as_python_constant():
                return true_fn.call_function(tx, operands.unpack_var_sequence(tx), {})
            else:
                return false_fn.call_function(tx, operands.unpack_var_sequence(tx), {})

        # predicate
        if type(pred.realize()) not in (
            ConstantVariable,
            TensorVariable,
            SymNodeVariable,
        ):
            unimplemented(
                gb_type="torch.cond: improper predicate",
                context=str(pred),
                explanation="Expected `pred` to be a bool or a boolean tensor with a single item "
                f"but got {str(type(pred))} with original python type {str(pred.python_type())}.",
                hints=[
                    *graph_break_hints.USER_ERROR,
                ],
            )

        # operands
        if not isinstance(operands, (ListVariable, TupleVariable)):
            unimplemented(
                gb_type="torch.cond: improper operands",
                context=str(operands),
                explanation="Expected `operands` to be a list/tuple "
                f"but got {operands.python_type()}.",
                hints=[
                    *graph_break_hints.USER_ERROR,
                ],
            )

        operands_seq = operands.unpack_var_sequence(tx)
        if not only_consist_of(
            operands, (TensorVariable, ConstantVariable, SymNodeVariable)
        ):
            unimplemented(
                gb_type="torch.cond: improper operands contents",
                context=str(operands),
                explanation="Expected `operands` to be a list/tuple of pytrees that only consists of tensor leaves.",
                hints=[
                    *graph_break_hints.USER_ERROR,
                ],
            )

        # branches
        _check_supported_callable_arg(tx, true_fn, "true_fn")
        _check_supported_callable_arg(tx, false_fn, "false_fn")

        # Our strategy for tracing the true/false branches of cond
        # are to checkpoint our graphstate, run the true branch,
        # roll it back to the checkpoint, and run the false
        # branch, and then merge the graphstates.  Well, perhaps
        # "merge" is too strong a word: we mostly assert that
        # the resulting graphstates have to be the same.
        #
        # We only permit guards to diverge (we union the guards from
        # both branches).  In particular, this means that side
        # effects are NOT permitted inside true/false branches; this
        # would be difficult to implement, because of the path
        # explosion problem.

        def speculate_branch(
            branch: bool,
        ) -> tuple[VariableTracker, OutputSpec, torch.fx.Graph, dict[Proxy, Proxy]]:
            # NB: 0 is predicate
            ix = 1 if branch else 2
            assert self._HOP_NAME is not None
            # TODO: Support kwargs
            (
                (ret_val, ret_spec),
                ret_graph,
                ret_lifted_freevars,
            ) = speculate_subgraph(
                tx,
                args[ix],
                operands_seq,
                {},
                self._HOP_NAME,
                source_target=self.value,
                should_flatten_outputs=True,
                # TODO - removing consts from control flow ops need more work
                remove_consts_from_outputs=False,
                supports_input_mutation=self.supports_input_mutation,
                supports_aliasing=self.supports_aliasing,
            )

            # need to ensure we increase epoch so we don't memoize unbacked bindings
            # across different subgraphs which can interfere with runtime assertion
            # generation.
            assert tx.fake_mode is not None
            tx.fake_mode.epoch += 1

            if not only_consist_of(ret_val, (TensorVariable, ConstantVariable)):
                unimplemented(
                    gb_type="torch.cond: unsupported branch return type",
                    context=str(ret_val),
                    explanation="Expected branches to return a possibly nested pytree of tensors or constant ints.",
                    hints=[
                        *graph_break_hints.USER_ERROR,
                    ],
                )
            for ret in ret_val.unpack_var_sequence(tx):
                if ret.is_python_constant() and not isinstance(
                    ret.as_python_constant(), int
                ):
                    unimplemented(
                        gb_type="torch.cond: unsupported branch return type (constant non-int)",
                        context=str(ret_val),
                        explanation="Constants returned from branches must be ints.",
                        hints=[
                            *graph_break_hints.USER_ERROR,
                        ],
                    )
            return ret_val, ret_spec, ret_graph, ret_lifted_freevars

        (true_r, true_spec, true_graph, true_lifted_freevars) = speculate_branch(True)
        true_nn_modules = dict(tx.output.nn_modules)

        (
            false_r,
            false_spec,
            false_graph,
            false_lifted_freevars,
        ) = speculate_branch(False)
        false_nn_modules = dict(tx.output.nn_modules)

        same_spec = _make_inlined(tx, pytree.TreeSpec.__eq__)(
            true_spec.treespec, false_spec.treespec
        ).as_python_constant()
        # 3.14: NotImplemented cannot be converted to bool
        if same_spec is not NotImplemented and not same_spec:
            unimplemented(
                gb_type="torch.cond: differing branch outputs",
                context=f"true_spec: {true_spec.treespec}, false_spec: {false_spec.treespec}, same_spec: {same_spec}",
                explanation="Expected branches to return the same pytree structure.",
                hints=[
                    *graph_break_hints.USER_ERROR,
                ],
            )

        (
            true_graph,
            false_graph,
            true_shared,
            _false_shared,
            unique_true,
            unique_false,
        ) = _merge_graph_inputs(
            true_graph,
            true_lifted_freevars,
            "true_branch",
            false_graph,
            false_lifted_freevars,
            "false_branch",
        )

        true_name = tx.output.install_subgraph(
            "cond_true",
            torch.fx.GraphModule(true_nn_modules, true_graph),
        )
        false_name = tx.output.install_subgraph(
            "cond_false",
            torch.fx.GraphModule(false_nn_modules, false_graph),
        )

        true_node = make_attr(tx, true_name)
        false_node = make_attr(tx, false_name)

        p_args = (
            pred.as_proxy(),
            true_node,
            false_node,
            # We pick true_shared but it shouldn't matter
            tuple(true_shared + unique_true + unique_false),
        )

        return _call_function_and_unflatten_output(
            tx,
            torch.ops.higher_order.cond,
            p_args,
            {},
            None,
            true_spec,
            true_r,
        )