def _validate_outputs_safe_for_autograd_nodes(
        self, rv: list["VariableTracker"], tx: "InstructionTranslatorBase"
    ) -> None:
        """
        Validate that if torch.autograd.grad is used in the graph and outputs
        require grad, we trigger AutogradGradRestartAnalysis only if the output is connected
        to the autograd.grad computation.

        rv here refers to list of variables that are being returned from dynamo graph.

        See Note [Tracing autograd.grad in dynamo]
        """
        if not self.autograd_grad_consumed_grad_fns:
            return

        from .variables.tensor import TensorVariable

        for var in rv:
            if not isinstance(var, TensorVariable) or not var.requires_grad:
                continue

            fake_tensor = var.as_proxy().node.meta.get("example_value")
            assert isinstance(fake_tensor, torch._subclasses.fake_tensor.FakeTensor)
            if fake_tensor.grad_fn is None:
                continue

            # Traverse the entire autograd graph of the returned tensor to check
            # if any node was consumed by autograd.grad
            reachable_grad_fns = collect_reachable_grad_fns([(fake_tensor, None)])
            if reachable_grad_fns & self.autograd_grad_consumed_grad_fns:
                # Record info about the leaked tensor for the error message
                tensor_name = str(var.source) if var.source else var.proxy.node.name
                tx.speculation_log.autograd_grad_leaked_tensors.append(tensor_name)

        if tx.speculation_log.autograd_grad_leaked_tensors:
            # Set the flag to graph break at autograd.grad on retry
            tx.speculation_log.graph_break_on_autograd_grad = True
            raise exc.AutogradGradRestartAnalysis(
                restart_reason="autograd.grad consumed grad_fns of returned tensors"
            )