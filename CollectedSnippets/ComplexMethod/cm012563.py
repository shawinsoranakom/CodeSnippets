def deduce_node_dtype(self, node: torch.fx.Node) -> torch.dtype | None:
        if node.op == "placeholder":
            return None

        if node.target == "output" and len(node.args) != 1:
            # we can infer output node if it only have 1 arg
            return None

        if node.target is operator.getitem:
            node_arg = node.args[0]
            assert isinstance(node_arg, torch.fx.Node), type(node_arg)
            return self.deduce_node_dtype(node_arg)

        assert isinstance(node.target, str), type(node.target)

        if node.target.startswith("masked_subblock"):
            return self.deduce_node_dtype_by_subgraph(node)

        if (
            output_dtype := deduce_output_dtype_by_name(
                node.target,
                *node.args,
                **node.kwargs,
            )
        ) is not None:
            return output_dtype

        return self.deduce_node_dtype_by_inputs(node)