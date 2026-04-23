def call_function(
        self,
        tx: "InstructionTranslator",
        args: Sequence[VariableTracker],
        kwargs: dict[str, VariableTracker],
    ) -> VariableTracker:
        """
        At the highest level, the goal of tracing an autograd.Function is to
        essentially emit a new autograd.Function object. To do this, Dynamo
        traces fwd and bwd graph and then inserts a AutogradFunctionApply HOP in
        the graph that call the traced fwd and bwd graph in the `forward` and
        `backward` methods respectively. AOTDispatcher desugars this HOP and
        just inlines the hop fwd and bwd into the main graph during its tracing.

        However, the traced forward and backward graphs cannot be directly
        placed in the new autograd.Function because autograd.Function has some
        requirements.

        a) # fwd graph inputs = # bwd graph outputs
        b) # fwd graph outputs = # bwd graph inputs
        c) Since the graphs do not have ctx variable, we have to manually return
        the saved_tensors from the forward and have additional inputs in the
        backward, and wire the connections.

        Unfortunately, reworking the initial traced fwd and bwd graphs to
        satisfy the above 3 conditions leads to a very tedious codebase.

        Lets look at an example

        class Foo:
            def __init__(self):
                self.a = 4

        class MySin(torch.autograd.Function):
            @staticmethod
            def forward(ctx, x, foo):
                ctx.save_for_backward(x)
                return x.sin() + foo.a

            @staticmethod
            def backward(ctx, grad):
                x, = ctx.saved_tensors
                return grad * x.cos()

        We want the resulting graphs to look like:

        # Note that Dynamo lifts the foo_a directly as an input.
        def fwd(ctx, x, foo_a):
            # (output, saved tensors / attrs)
            return (x.sin() + foo_a, (x))

        # Note that backward graph has None as the second output to match the
        # fwd requirements (even though the original backward function has just
        # output)
        def bwd(ctx, grad, x):
            return grad * x.cos(), None


        To accomplish this, we're going to:
        1. Construct a ctx object
        2. Speculate subgraph forward
        3. Speculate subgraph backward
        4. rewired_bwd_graph_inputs - Use the traced fwd graph as the anchor point, and rewire the backward graph outputs
        5. handle_saved_tensors_wiring - Handle the saved tensors, as mentioned in (c)
        """

        fwd_tracer = torch._dynamo.output_graph.SubgraphTracer(
            tx.output,
            parent=tx.output.current_tracer,
            source_target=self._HOP_NAME,
        )

        ctx = self.prepare_ctx_vt(tx, args, kwargs)

        fwd_fn, fwd_out, fwd_graph, fwd_freevars, fwd_graph_output_vts = (
            self.trace_forward_graph(tx, ctx, fwd_tracer, args, kwargs)
        )

        bwd_args, bwd_out, bwd_graph, bwd_freevars, bwd_graph_output_vts = (
            self.trace_backward_graph(tx, ctx, fwd_tracer, fwd_out, fwd_fn)
        )

        self.rewire_bwd_graph_outputs(
            fwd_freevars, bwd_out, bwd_graph, bwd_freevars, args
        )

        fwd_graph, bwd_graph = self.handle_saved_tensors_wiring(
            fwd_out,
            fwd_graph,
            fwd_freevars,
            fwd_graph_output_vts,  # type: ignore[arg-type]
            bwd_graph,
            bwd_freevars,
        )

        # If users call ctx.mark_non_differentiable, we should capture these output tensors who
        # are marked as non-differentiable and pass them to ApplyTemplate
        # at torch._functorch.autograd_function.AutogradFunctionApply for reconstruction.
        non_differentiable_idx = []
        if ctx.non_differentiable is not None:
            non_differentiable_set = set(ctx.non_differentiable)
            assert isinstance(fwd_out, variables.BaseListVariable)
            for i, x in enumerate(fwd_out.items):
                if x.is_tensor() and x.as_proxy() in non_differentiable_set:
                    non_differentiable_idx.append(i)

        # See Note [Activations with no version counter checks in eager]
        # Compute which tensors in bwd_freevars came from ctx.save_for_backward.
        # This allows AOT autograd to distinguish between tensors saved via
        # save_for_backward vs those stashed directly on ctx (e.g., ctx.x = x).
        saved_for_backward_idx = []
        if ctx.saved_tensors is not None and len(ctx.saved_tensors.tensors) > 0:
            # Build a set of proxies that were passed to save_for_backward
            saved_tensor_proxies = OrderedSet()
            for tensor_vt in ctx.saved_tensors.tensors:
                if tensor_vt.is_tensor():
                    saved_tensor_proxies.add(tensor_vt.as_proxy())

            # bwd_freevars is a dict of outer-graph proxy -> inner-graph proxy
            # for all tensors passed from fwd to bwd. Find which indices
            # correspond to save_for_backward tensors.
            for i, fwd_proxy in enumerate(bwd_freevars.keys()):
                if fwd_proxy in saved_tensor_proxies:
                    saved_for_backward_idx.append(i)

        # Store fwd_body
        fwd_nn_modules = tx.output.tracing_context.module_context.copy_graphstate()
        fwd_name = tx.output.install_subgraph(
            "fwd_body",
            torch.fx.GraphModule(fwd_nn_modules.nn_modules, fwd_graph),
        )
        fwd_node = make_attr(tx, fwd_name)

        # Store bwd_body
        bwd_nn_modules = tx.output.tracing_context.module_context.copy_graphstate()
        bwd_name = tx.output.install_subgraph(
            "bwd_body",
            torch.fx.GraphModule(bwd_nn_modules.nn_modules, bwd_graph),
        )
        bwd_node = make_attr(tx, bwd_name)

        p_args = (
            fwd_node,
            bwd_node,
            *list(fwd_freevars.keys()),
        )
        kwargs_for_fn = {
            "non_differentiable_idx": non_differentiable_idx,
            "saved_for_backward_idx": saved_for_backward_idx,
        }

        # Store the invocation as a call
        from torch._functorch.autograd_function import autograd_function_apply

        # We use speculate_subgraph to get the fwd graph, but it's always under no grad mode like what eager mode does.
        # The fwd outputs (tensor's example_value) need to be inferred from fake tensor prop to get the correct attributes
        # (e.g, tensor.requires_grad), which would be used by downstream Dynamo tracing.
        # Since there can be other ops like Triton kernels, which depends on python dispatcher, we have to enable it.
        # TODO - revisit if we need the python dispatcher
        with enable_python_dispatcher():
            with tx.output.fake_mode:
                fwd_freevars_args = [_get_fake_value(arg) for arg in fwd_freevars]

                example_value = autograd_function_apply(
                    tx.output.nn_modules[fwd_node.node.name],
                    tx.output.nn_modules[bwd_node.node.name],
                    *fwd_freevars_args,
                    **kwargs_for_fn,
                )

        flat_variable = add_call_function(
            tx, autograd_function_apply, p_args, kwargs_for_fn, example_value
        )
        # type: ignore[arg-type]
        overwrite_tensor_vt_proxy(fwd_graph_output_vts, flat_variable)
        # type: ignore[arg-type]
        overwrite_tensor_vt_requires_grad(fwd_graph_output_vts, flat_variable)
        return fwd_out