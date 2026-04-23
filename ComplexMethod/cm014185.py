def trace_backward_graph(
        self,
        tx: "InstructionTranslator",
        ctx: "AutogradFunctionContextVariable",
        fwd_tracer: "SubgraphTracer",
        fwd_out: VariableTracker,
        fwd_fn: VariableTracker,
    ) -> tuple[
        Sequence[VariableTracker],
        VariableTracker,
        torch.fx.Graph,
        dict[Proxy, Proxy],
        VariableTracker | tuple[VariableTracker, ...],
    ]:
        """
        Traces the backward method of the autograd.Function object.
        """
        from . import UserMethodVariable

        # Note that for the forward, we do not restore side effects, because we
        # want the later tracing to see the side-effects. But for backward, we
        # are just trying to capture the graph, and therefore we must restore
        # the side effects.
        prev_side_effects = tx.output.side_effects

        # Speculate subgraph on the backward. We make the bwd tracer a child of
        # the fwd tracer, because backward may rely on tensors/attrs created in
        # the fwd tracer.
        bwd_tracer = torch._dynamo.output_graph.SubgraphTracer(
            tx.output,
            parent=fwd_tracer,
            source_target=self._HOP_NAME,
        )

        bwd_args = []
        if fwd_out.is_tensor():
            bwd_args.append(fwd_out)
        else:
            assert isinstance(fwd_out, variables.BaseListVariable)
            for i in fwd_out.items:
                if i.is_tensor():
                    bwd_args.append(i)
                else:
                    bwd_args.append(ConstantVariable.create(None))

        bwd_fn, bwd_args = self.prepare_fn_vt(tx, ctx, "backward", bwd_args)

        def is_strict_for(v: VariableTracker) -> bool:
            if v.is_tensor():
                # we can be more lax for stuff from forward
                return v.proxy.tracer is not fwd_tracer  # type: ignore[attr-defined]
            return True

        # automatic_with_forced_inputs relies on the function arg names to
        # create a new proxy. Also, it will always INSERT a tensor placeholder
        # as input, even though it might not be used in the graph. This allows
        # us to make a mapping for the backward graph.
        with (
            tx.output.subtracer(fwd_fn, fwd_tracer),  # type: ignore[arg-type]
            tx.strict_translation_mode(is_strict_for),
        ):
            try:
                bwd_out, bwd_graph, bwd_freevars, bwd_graph_output_vts, _ = (
                    speculate_subgraph_with_auto_output_flattening(
                        tx,
                        bwd_fn,
                        bwd_args,
                        {},
                        self._HOP_NAME,
                        # TODO - revisit if we need enable_grad
                        enable_grad=False,
                        set_subgraph_inputs="automatic_with_forced_inputs",
                        allow_side_effects=False,
                        tracer=bwd_tracer,
                    )
                )
            except torch._dynamo.exc.UnknownPropertiesDuringBackwardTrace as e:
                # TODO - Do not support this path because of eager
                # divergence forced by contiguous calls. Instead suggested
                # nonstrict_trace.
                from unittest import mock

                bwd_tracer = torch._dynamo.output_graph.SubgraphTracer(
                    tx.output,
                    parent=fwd_tracer,
                    source_target=self._HOP_NAME,
                )
                from .._trace_wrapped_higher_order_op import (
                    autograd_function_backward_rewritten,
                )
                from .builder import SourcelessBuilder

                if isinstance(self.bwd_fn, types.FunctionType):
                    bwd_fn = SourcelessBuilder.create(
                        tx, autograd_function_backward_rewritten(self.bwd_fn)
                    )
                elif isinstance(self.bwd_fn, types.MethodType):
                    bwd_fn = UserMethodVariable(
                        autograd_function_backward_rewritten(self.bwd_fn.__func__),
                        VariableTracker.build(tx, self.bwd_fn.__class__),
                    )
                else:
                    unimplemented(
                        gb_type="autograd.Function.apply: non-function or method backward (2)",
                        context=str(self.bwd_fn),
                        explanation="Expected backward function to be a function or method.",
                        hints=[],
                        from_exc=e,
                    )

                with mock.patch(
                    "torch._dynamo.config._autograd_backward_strict_mode_conditional_banned_ops",
                    [],
                ):
                    bwd_out, bwd_graph, bwd_freevars, bwd_graph_output_vts, _ = (
                        speculate_subgraph_with_auto_output_flattening(
                            tx,
                            bwd_fn,
                            bwd_args,
                            {},
                            self._HOP_NAME,
                            enable_grad=False,
                            set_subgraph_inputs="automatic_with_forced_inputs",
                            allow_side_effects=False,
                            tracer=bwd_tracer,
                        )
                    )

        # Restore the side effects
        tx.output.side_effects = prev_side_effects

        return bwd_args, bwd_out, bwd_graph, bwd_freevars, bwd_graph_output_vts