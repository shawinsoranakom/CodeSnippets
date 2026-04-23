def _deduce_value(self, node: torch.fx.Node) -> Any:
        if self.lifted_constant_names is None:
            return super().run_node(node)
        # if lifted_constant_names is passed in, no concrete value is available
        # so we just check if all inputs have values
        if self.skip_folding_node_fn is not None and self.skip_folding_node_fn(node):
            return self.unknown_value
        flattened_node_inps = pytree.arg_tree_leaves(*node.args, **node.kwargs)
        for inp in flattened_node_inps:
            if (
                isinstance(inp, torch.fx.Node)
                and inp.name not in (self.lifted_constant_names or ())
                and self.env[inp] is not self.deferred_value
            ):
                return self.unknown_value
        return self.deferred_value