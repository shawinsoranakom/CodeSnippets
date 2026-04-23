def _check_requires_grad_intermediate_outputs(
        self, rv: list["VariableTracker"], tx: "InstructionTranslatorBase"
    ) -> None:
        """Skip frame if a source-less requires_grad_() intermediate leaks as output.

        AOTAutograd's functionalization drops requires_grad_() on intermediates,
        so returning them (or tensors derived from them) produces wrong results.
        We detect this via FX graph reachability: find the requires_grad_() nodes
        for source-less intermediates, then check if any output is downstream.
        """
        from .variables.tensor import TensorVariable

        # Collect FX nodes for source-less requires_grad_() intermediates
        tainted_nodes: set[torch.fx.Node] = set()
        for v in self.leaf_var_creation_order:
            if isinstance(v, TensorVariable) and not v.source:
                tainted_nodes.add(v.as_proxy().node)

        if not tainted_nodes:
            return

        # Propagate taint forward through the FX graph
        for node in self.graph.nodes:
            if node in tainted_nodes:
                continue
            if any(inp in tainted_nodes for inp in node.all_input_nodes):
                tainted_nodes.add(node)

        # Check leaked outputs: tainted + requires_grad means the output
        # carries autograd state that AOTAutograd would silently drop.
        # Detached outputs (requires_grad=False) are fine — no autograd to lose.
        for var in rv:
            if (
                isinstance(var, TensorVariable)
                and var.requires_grad
                and var.as_proxy().node in tainted_nodes
            ):
                msg = (
                    "An intermediate tensor that had requires_grad_() called "
                    "on it (or a tensor derived from it) is being returned "
                    "from the compiled region. AOTAutograd's functionalization "
                    "drops the requires_grad_() effect on graph outputs, "
                    "producing wrong results. If you only need the tensor "
                    "values without gradients, call .detach() before returning."
                )
                if tx.one_graph:
                    unimplemented(
                        gb_type="returning intermediate with requires_grad_()",
                        context="graph output depends on source-less requires_grad_()",
                        explanation=msg,
                        hints=[
                            "If you only need the tensor values without gradients, "
                            "call .detach() before returning.",
                            "Consume the gradient inside the compiled function "
                            "(call backward() and use .grad), "
                            "or move requires_grad_() outside torch.compile.",
                        ],
                    )
                else:
                    tx.speculation_log.graph_break_on_requires_grad_ = True
                    raise exc.RequiresGradRestartAnalysis(
                        restart_reason="source-less requires_grad_() intermediate leaked as output"
                    )