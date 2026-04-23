def _mark_complex_exprs_as_must_recompute(self) -> None:
        """
        For control flow operators such as scan, we don't want to
        have symint in the partitioning boundaries because otherwise we would need to support stacking
        the symints up, which causes more entropy in the stack.

        By marking the recompute polify for complex nodes as MUST_RECOMPUTE, the partitioning boundary
        no longer contains complex expressions.

        Note that this pass doesn't exclude basic symbols from partitioning boundary
        and it's up to the downstream to decide whether to return the basic symbol
        or have a separate graph pass to remove them.
        """

        from torch._functorch.partitioners import CheckpointPolicy

        for n in (
            node for node in self.joint_gm.graph.nodes if node.op == "call_function"
        ):
            if "val" not in n.meta:
                continue
            val = n.meta["val"]
            if isinstance(val, torch.SymInt) and is_complex_expr(val.node.expr):
                if n.meta.get("recompute", None) is not None:
                    raise AssertionError(
                        f"node {n} with complex SymInt expression should not have recompute policy set"
                    )

                n.meta["recompute"] = CheckpointPolicy.MUST_RECOMPUTE

        self.joint_gm.graph.lint()
        self.joint_gm.recompile()