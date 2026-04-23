def _collect_backward_inputs(
        self, vars_iter: Iterable[VariableTracker], error_on_non_leaf: bool = False
    ) -> list[VariableTracker] | None:
        """
        Collect unique leaf tensors from vars_iter for backward.

        Only collects leaf tensors (no grad_fn). Non-leaf tensors are skipped
        (or error if error_on_non_leaf=True) because when auto-detecting inputs,
        we must not stop gradients at non-leafs - they are intermediates, and the
        real leaf tensors (parameters) are further up the autograd graph.

        Deduplicates by proxy.node.
        Returns list of unique leaf tensor variables.
        """
        from ..source import SyntheticLocalSource

        result = []
        seen_nodes: set[torch.fx.Node] = set()
        for var in vars_iter:
            if isinstance(var, TensorVariable) and var.requires_grad:
                # Non-leaf tensors (has_grad_fn=True) must be skipped because:
                # 1. Semantically: they're intermediates, not the leaves we want gradients for
                # 2. Implementation: accumulate_grad polyfill can't handle .grad on non-leafs
                #    (Dynamo creates GetAttrVariable instead of TensorVariable)
                #
                # In-graph created tensors without proper source also can't be handled
                # when user explicitly passes them as inputs, because
                # subguards_allowed() returns False for SyntheticLocalSource.
                # However, in auto-detect mode (error_on_non_leaf=False), source-less
                # leaves are valid backward targets — they gained requires_grad via
                # requires_grad_() and accumulate_grad_ writes to .grad directly.
                if var.has_grad_fn:
                    if error_on_non_leaf:
                        unimplemented(
                            gb_type="backward() with non-leaf tensor",
                            context=f"backward(inputs=[...]) with non-leaf tensor: {var}",
                            explanation="backward(inputs=[...]) with non-leaf tensors is not yet supported.",
                            hints=[
                                "Only pass leaf tensors (parameters, graph inputs) to backward(inputs=...)",
                            ],
                        )
                elif error_on_non_leaf and (
                    not var.source or isinstance(var.source, SyntheticLocalSource)
                ):
                    unimplemented(
                        gb_type="backward() with in-graph created tensor",
                        context=f"backward(inputs=[...]) with in-graph created tensor: {var}",
                        explanation="backward(inputs=[...]) with tensors created inside the "
                        "compiled function is not yet supported.",
                        hints=[
                            "Only pass tensors that are inputs to the compiled function or captured from outside",
                        ],
                    )
                else:
                    node = var.proxy.node
                    if node not in seen_nodes:
                        seen_nodes.add(node)
                        result.append(var)
        # pyrefly: ignore [bad-return]
        return result