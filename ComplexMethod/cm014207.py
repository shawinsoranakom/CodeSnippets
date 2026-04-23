def method_requires_grad_(
        self, tx: "InstructionTranslator", requires_grad: bool | VariableTracker = True
    ) -> VariableTracker:
        if requires_grad is not True:
            requires_grad = requires_grad.as_python_constant()  # type: ignore[attr-defined]

        node = self.as_proxy().node
        example_value = node.meta["example_value"]
        if example_value.requires_grad != requires_grad:
            # For graph inputs (tensors with source), requires_grad_() is a
            # metadata mutation that we can't trace — graph break as before.
            if self.source:
                unimplemented(
                    gb_type="Unsupported Tensor.requires_grad_() call",
                    context=f"call_method {self} requires_grad_",
                    explanation="Dynamo does not support changes to a Tensor's "
                    "`requires_grad` through calling `requires_grad_()`.",
                    hints=[],
                )
            # On a previous attempt, we traced through requires_grad_() but
            # discovered at compile time that the tainted intermediate leaked
            # as a graph output. Graph break here to preserve partial
            # acceleration for code before requires_grad_().
            if tx.speculation_log.graph_break_on_requires_grad_:
                unimplemented(
                    gb_type="requires_grad_() intermediate leaked as output",
                    context=f"call_method {self} requires_grad_",
                    explanation="An intermediate tensor with requires_grad_() called "
                    "on it (or a tensor derived from it) is returned from the "
                    "compiled region. Graph breaking here to preserve partial "
                    "acceleration.",
                    hints=[
                        "Call .detach() before returning if you only need values.",
                        "Consume the gradient inside the compiled function "
                        "(call backward() and use .grad), "
                        "or move requires_grad_() outside torch.compile.",
                    ],
                )
            # AOTAutograd re-traces the FX graph under functorch transforms
            # (functionalization). Functorch's checkSupportsInplaceRequiresGrad()
            # rejects requires_grad_() when the dynamic layer stack is non-empty.
            # We wrap the call with set_inplace_requires_grad_allowed(True) to
            # bypass this check, matching GradInplaceRequiresGradCtxManagerVariable
            # in ctx_manager.py (which handles the explicit context manager case).
            #
            # Lines below do two things in parallel:
            # 1. Mutate trace-time state so example_value.requires_grad_() works
            # 2. Emit FX nodes so the same toggle happens during AOTAutograd re-trace
            prev_state = torch._C._functorch.get_inplace_requires_grad_allowed()
            torch._C._functorch.set_inplace_requires_grad_allowed(True)
            try:
                tx.output.create_node(
                    "call_function",
                    torch._C._functorch.set_inplace_requires_grad_allowed,
                    (True,),
                    {},
                )
                tx.output.create_proxy(
                    "call_method",
                    "requires_grad_",
                    (self.as_proxy(),),
                    {},
                )
                tx.output.create_node(
                    "call_function",
                    torch._C._functorch.set_inplace_requires_grad_allowed,
                    (prev_state,),
                    {},
                )
            finally:
                torch._C._functorch.set_inplace_requires_grad_allowed(prev_state)
            example_value.requires_grad_(requires_grad)
            self.requires_grad = requires_grad
            if requires_grad:
                tx.output.leaf_var_creation_order.append(self)
                # For source-less intermediates, initialize .grad = None in
                # side effects so the accumulate_grad polyfill can read/write
                # .grad naturally. Graph inputs don't need this — they handle
                # .grad through their source.
                if not self.source and tx.output.side_effects.is_attribute_mutation(
                    self
                ):
                    tx.output.side_effects.store_attr(
                        self, "grad", variables.ConstantVariable.create(None)
                    )
        return self