def _create_proxy(
        self,
        kind: str,
        target: Any,
        args: Any,
        kwargs: Any,
        name: str | None = None,
        type_expr: Any | None = None,
        proxy_factory_fn: Callable[[fx.Node], fx.Proxy] | None = None,
    ) -> fx.Proxy:
        # NOTE: [Nested SubgraphTracer and free_variable handling]
        # --------------------------------------------------------
        # Read NOTE [HigherOrderOperator tracing design] first.
        #
        # Let's say we're in the middle of introspecting the body of a possibly
        # nested HigherOrderOperator, and we see a free variable.
        #
        # There are two cases:
        # 1. We see a free variable that is already tracked by Dynamo.
        # 2. We see a free variable that has not been tracked by Dynamo
        #
        # In case 1, we call `maybe_lift_tracked_freevar_to_input` (below)
        # which will lift the freevar to be an input of this subgraph
        # and also recursively lift it to be an input on the parent(s).
        #
        # In case 2, before the call to `create_proxy`, the InstructionTranslator
        # will see the freevar when it gets loaded by Python bytecode.
        # E.g. for Python 3.11 the bytecodes that may do this are LOAD_DEREF or
        # LOAD_GLOBAL.
        # There, the InstructionTranslator asks Dynamo to begin tracking the
        # freevar by building a new Variable.
        # Building a new Variable automatically lifts the freevar to be an
        # input of the root SubgraphTracer.
        #
        # The implications for the code below are:
        # - We will always be in Case 1 when we get to this code.
        # - Any "free variable" we encounter here is guaranteed to already be
        #   bound, that is, it is either a graph input of the root graph, or
        #   some local variable of the root graph or a subgraph.
        # - The additional work we need to do here is *only* that we need to
        #   lift this free variable into inputs (recursively) of each nested
        #   higher-order-op subgraph until we hit the subgraph where the free
        #   variable is bound
        if self.parent is not None:
            flat_args, tree_spec = pytree.tree_flatten((args, kwargs))
            new_flat_args = []
            for arg in flat_args:
                maybe_new_arg = self.maybe_lift_tracked_freevar_to_input(arg)
                new_flat_args.append(maybe_new_arg)

            args, kwargs = pytree.tree_unflatten(new_flat_args, tree_spec)

        rv = super().create_proxy(
            kind,
            target,
            args,
            kwargs,
            name,
            type_expr,
            proxy_factory_fn,  # type: ignore[arg-type]
        )

        # append stack trace to fx node
        tx = self.output_graph.current_tx

        # log detailed location of line of code in 3.11
        if sys.version_info >= (3, 11) and kind in (
            "call_function",
            "call_method",
            "call_module",
        ):
            cur_inst = tx.current_instruction
            if (
                cur_inst is not self.prev_inst
                and cur_inst.positions is not None
                and cur_inst.positions.lineno is not None
            ):
                tx_code = tx.f_code
                header = tx.get_line_of_code_header(lineno=cur_inst.positions.lineno)

                def get_trace_call_log_str() -> str:
                    line = get_instruction_source_311(tx_code, cur_inst).rstrip()
                    return f"TRACE FX call {rv.node.name} from {header}\n{line}"

                trace_call_log.debug("%s", LazyString(get_trace_call_log_str))
                self.prev_inst = cur_inst

        # update reference to original meta if we're tracing a new code object
        is_retracing = False
        if tx.f_code is not self._cur_code:
            orig_graphmodule_maybe = code_context.get_context(tx.f_code).get(
                "orig_graphmodule", lambda: None
            )()
            if isinstance(orig_graphmodule_maybe, torch.fx.GraphModule):
                is_retracing = True
                self._orig_gm_meta = [
                    nd.meta for nd in orig_graphmodule_maybe.graph.nodes
                ]
                self._orig_gm_lineno_map = orig_graphmodule_maybe._lineno_map
                self._orig_gm_firstlineno = (
                    orig_graphmodule_maybe.forward.__code__.co_firstlineno
                )
            else:
                self._orig_gm_meta = None
                self._orig_gm_lineno_map = None
                self._orig_gm_firstlineno = None
        nn_module_stack = tx.nn_module_stack
        if nn_module_stack:
            rv.node.meta["nn_module_stack"] = nn_module_stack.copy()

        if kind in {"call_function", "call_method"}:
            stack = (rv.node.name, target)
            if nn_module_stack:
                # Current codebase assumes that the nn_module_stack has the
                # builtin modules in the stack.
                current_nn_module = list(rv.node.meta["nn_module_stack"].values())[-1][
                    1
                ]
                if current_nn_module.__module__.startswith(
                    ("torch.nn.modules", "torch.ao.")
                ) and not current_nn_module.__module__.startswith(
                    "torch.nn.modules.container"
                ):
                    stack = (rv.node.name, current_nn_module)

            rv.node.meta["source_fn_stack"] = self.source_fn_stack + [stack]
        elif kind == "call_module":
            if self.parent is not None:
                unimplemented(
                    gb_type="Invoking an nn.Module inside a higher order operator",
                    context=f"Higher order op name: {self.source_target}",
                    explanation="This is not supported.",
                    hints=[],
                )
            # For modules we store the class
            rv.node.meta["source_fn_stack"] = self.source_fn_stack + [
                (
                    rv.node.name,
                    next(
                        ty
                        for k, (_, ty) in rv.node.meta["nn_module_stack"].items()
                        if k.split("@")[0] == target
                    ),
                )
            ]

        self._maybe_preserve_original_meta(tx, rv.node)

        if not is_retracing:
            if "nn_module_stack" not in rv.node.meta:
                nn_module_stack = tx.nn_module_stack
                if nn_module_stack:
                    rv.node.meta["nn_module_stack"] = nn_module_stack.copy()

            if "source_fn_stack" not in rv.node.meta:
                if kind in {"call_function", "call_method"}:
                    rv.node.meta["source_fn_stack"] = self.source_fn_stack + [
                        (rv.node.name, target)
                    ]
                elif kind == "call_module":
                    if self.parent is not None:
                        unimplemented(
                            gb_type="Invoking an nn.Module inside a HigherOrderOperator",
                            context="",
                            explanation="This is not supported.",
                            hints=[],
                        )
                    # For modules we store the class
                    rv.node.meta["source_fn_stack"] = self.source_fn_stack + [
                        (
                            rv.node.name,
                            rv.node.meta["nn_module_stack"][target][1],
                        )
                    ]

        if "stack_trace" not in rv.node.meta:
            frame_summaries: list[traceback.FrameSummary] = []
            while tx:
                # Avoid frame summaries from inside the torch/nn/modules. This ensures that we keep the stack trace of
                # the user code.
                if not tx.is_co_filename_from_nn_modules():
                    frame_summaries.append(tx.frame_summary())
                tx = getattr(tx, "parent", None)

            filtered_frame_summaries = [
                frame
                for frame in frame_summaries
                if frame.filename not in uninteresting_files()
            ]

            # Reverse the frame_summaries, such that the innermost frame is at the last
            filtered_frame_summaries.reverse()

            # official from_list stub doesn't have new-style type
            msgs = traceback.StackSummary.from_list(filtered_frame_summaries).format()
            rv.node.stack_trace = "".join(msgs)

        if (
            torch._dynamo.config.use_graph_deduplication
            or torch._dynamo.config.track_nodes_for_deduplication
        ):
            self.output_graph.region_tracker.track_node(
                self.output_graph.current_tx, rv.node
            )
        return rv