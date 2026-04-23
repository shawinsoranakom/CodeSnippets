def handle_functorch_autograd_grad(
            self,
            tx: "InstructionTranslator",
            *args: VariableTracker,
            **kwargs: VariableTracker,
        ) -> VariableTracker | None:
            """Graph-break when closure-captured tensors lose their grad_fn.

            NOTE [Detecting lost autograd linkage in closure-captured tensors]

            Functorch transforms (vjp, grad, jacrev) return closures that capture
            tensors with grad_fn. When such a closure is compiled separately, those
            tensors become graph placeholders whose FakeTensors lose grad_fn,
            causing _autograd_grad to silently return zeros.

            _collect_placeholder_nodes gathers placeholder nodes from the
            outputs/inputs args. For each, we compare grapharg.example (the real
            tensor, retains grad_fn) against example_value (FakeTensor, grad_fn
            is None). A mismatch means autograd linkage was lost, so we
            graph-break.

            This is a pre-check only: kwargs (retain_graph, create_graph,
            grad_outputs) don't affect linkage detection and are handled by
            the default proxy path when this returns None.
            """
            outputs_var = args[0] if len(args) >= 1 else None
            inputs_var = args[1] if len(args) >= 2 else None

            if outputs_var is None or inputs_var is None:
                return None

            output_placeholder_nodes = _collect_placeholder_nodes(outputs_var)
            input_placeholder_nodes = _collect_placeholder_nodes(inputs_var)

            if output_placeholder_nodes and input_placeholder_nodes:
                for node in output_placeholder_nodes:
                    fake = node.meta.get("example_value")
                    grapharg = node.meta.get("grapharg")
                    if (
                        grapharg is not None
                        and isinstance(fake, torch.Tensor)
                        and fake.grad_fn is None
                    ):
                        real = grapharg.example
                        if isinstance(real, torch.Tensor) and real.grad_fn is not None:
                            unimplemented(
                                gb_type="_autograd_grad with lost grad_fn linkage",
                                context="outputs lost autograd linkage during tracing",
                                explanation=(
                                    "_autograd_grad() received tensors whose grad_fn "
                                    "was lost during tracing - this silently produces "
                                    "zero gradients."
                                ),
                                hints=[
                                    "Compile the full transform instead of the returned "
                                    "closure: torch.compile(lambda x: torch.func.vjp(f, x))",
                                    *graph_break_hints.SUPPORTABLE,
                                ],
                            )
            return None