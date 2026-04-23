def _remove_redundant_sym_size_ops(self) -> None:
        """
        Deletes torch.ops.sym_size.int operators whose output is a
        corresponding placeholder that holds the same symbol, and replace all usage
        of the sym_size node to be directly using the placeholders.

        This is to make sure all basic symbols come from inputs.
        """
        placeholder_exprs = {}
        for node in self.joint_gm.graph.nodes:
            if (
                isinstance(node, torch.fx.Node)
                and node.op == "placeholder"
                and hasattr(node, "meta")
                and "val" in node.meta
            ):
                val = node.meta["val"]
                if isinstance(val, torch.SymInt):
                    placeholder_exprs[val.node.expr] = node

        nodes_to_remove = []
        for node in self.joint_gm.graph.find_nodes(
            op="call_function", target=torch.ops.aten.sym_size.int
        ):
            if not (hasattr(node, "meta") and "val" in node.meta):
                raise AssertionError(
                    f"node {node} must have 'meta' attribute with 'val' key"
                )
            val = node.meta["val"]
            expr = val.node.expr
            if expr in placeholder_exprs:
                placeholder_node = placeholder_exprs[expr]
                node.replace_all_uses_with(placeholder_node)
                nodes_to_remove.append(node)

        for node in nodes_to_remove:
            self.joint_gm.graph.erase_node(node)

        self.joint_gm.graph.lint()
        self.joint_gm.recompile()