def method_backward(
        self,
        tx: "InstructionTranslator",
        gradient: VariableTracker | None = None,
        retain_graph: VariableTracker | None = None,
        create_graph: VariableTracker | None = None,
        inputs: VariableTracker | None = None,
    ) -> VariableTracker | None:
        """
        Trace tensor.backward() by rewriting as autograd.grad() + accumulate_grad.

        Implementation:
        1. Collect leaf tensors to compute gradients for
        2. Call autograd.grad(loss, inputs) to compute gradients
        3. For each leaf tensor, call accumulate_grad to update .grad

        Non-leaf tensor handling:
        - Auto-detect (inputs=None): Non-leaf tensors are silently skipped.
          This matches eager where only leaves get .grad.
        - User-provided (inputs=[...]): Errors if any non-leaf tensor is found.
          While eager backward(inputs=[non_leaf]) works, Dynamo cannot trace it
          because the accumulate_grad polyfill accesses .grad, and Dynamo creates
          a generic GetAttrVariable for .grad on non-leaf tensors (instead of a
          TensorVariable), which cannot be used in tensor operations.

        TODO: Support non-leaf tensors by fixing .grad access on non-leaf in Dynamo.
        """
        if not config.trace_autograd_ops:
            unimplemented(
                gb_type="Unsupported Tensor.backward() call",
                context=f"call_method {self} backward {gradient} {retain_graph} {create_graph} {inputs}",
                explanation="Dynamo currently does not support tracing `Tensor.backward()` when trace_autograd_ops is off.",
                hints=["Set torch._dynamo.trace_autograd_ops=True"],
            )

        if not self.requires_grad and not self.has_grad_fn:
            raise TorchRuntimeError(
                "tensor does not require grad and does not have a grad_fn"
            )

        # Step 1: Collect leaf tensors to compute gradients for
        #
        # Note: We rely on the autograd.grad handler to validate that the generated
        # autograd.grad call is legal (i.e., doesn't traverse external grad_fns).
        # If the loss depends on leaves we don't know about, the autograd.grad
        # handler will catch it via the external_grad_fns check.
        auto_detect = inputs is None
        if auto_detect:
            # Sources can be either user inputs (params are included here)
            # or parameters that are created in forward.
            all_vars = chain(
                tx.output.leaf_var_creation_order,
                tx.output.input_source_to_var.values(),
            )
            input_vars = self._collect_backward_inputs(all_vars)
            if not input_vars:
                # No leaf tensors found - nothing to accumulate gradients into.
                # This matches eager behavior where backward() is a no-op if there
                # are no leaves requiring grad.
                return ConstantVariable.create(None)
        else:
            provided_vars = (
                inputs.items
                if isinstance(inputs, variables.BaseListVariable)
                else [inputs]
            )
            input_vars = self._collect_backward_inputs(
                provided_vars, error_on_non_leaf=True
            )
            if not input_vars:
                # User explicitly provided inputs but none were valid leaf tensors.
                # This would cause "grad requires non-empty inputs" error at runtime.
                unimplemented(
                    gb_type="backward() with empty inputs",
                    context="backward(inputs=[...]) resulted in no valid leaf tensors",
                    explanation="backward(inputs=[...]) requires at least one valid leaf tensor.",
                    hints=[
                        "Ensure at least one tensor in inputs is a leaf (requires_grad=True, no grad_fn)",
                    ],
                )

        # Build autograd.grad call
        grad_kwargs = {"allow_unused": VariableTracker.build(tx, auto_detect)}
        if retain_graph is not None:
            grad_kwargs["retain_graph"] = retain_graph
        if create_graph is not None:
            grad_kwargs["create_graph"] = create_graph

        inputs_var = VariableTracker.build(tx, input_vars)
        grad_args = [self, inputs_var]
        if gradient is not None:
            grad_args.append(gradient)

        autograd_grad_fn = VariableTracker.build(tx, torch.autograd.grad)
        grads_var = autograd_grad_fn.call_function(tx, grad_args, grad_kwargs)

        # Accumulate gradients for unique leaf tensors under no_grad context
        # to replicate eager autograd engine.
        from .ctx_manager import GradModeVariable

        grad_mode_var = GradModeVariable.create(tx, False, initialized=True)
        grad_mode_var.enter(tx)

        accumulate_grad_fn = VariableTracker.build(
            tx, torch.ops.inductor.accumulate_grad_.default
        )
        assert input_vars is not None
        for idx, input_var in enumerate(input_vars):
            grad_i = grads_var.call_method(
                tx, "__getitem__", [VariableTracker.build(tx, idx)], {}
            )
            accumulate_grad_fn.call_function(tx, [input_var, grad_i], {})

        grad_mode_var.exit(tx)

        return ConstantVariable.create(None)