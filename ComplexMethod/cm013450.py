def _subgraph_has_impure_ops(module: torch.fx.GraphModule) -> bool:
        """
        Return True if a GraphModule type subgraph contains any impure op, else False.
        """
        if not isinstance(module, torch.fx.GraphModule):
            raise AssertionError(
                "caller should only pass GraphModule to subgraph_has_impure_ops check"
            )
        for node in module.graph.nodes:
            if node.op == "call_function" and node.is_impure():
                return True
            if (
                node.op == "call_module"
                # pyrefly: ignore [not-callable]
                and (submodule := module.get_submodule(node.target))
                and isinstance(submodule, torch.fx.GraphModule)
            ):
                return _subgraph_has_impure_ops(submodule)
        return False