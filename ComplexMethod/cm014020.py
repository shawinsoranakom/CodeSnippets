def cleanup_graph(self) -> None:
        """
        Remove "creation_timestamp" from node meta

        Remove this pattern from the graph:
            torch._C._set_grad_enabled(False)
            torch._C._set_grad_enabled(True)
        """
        assert self.should_exit
        nodes = list(self.graph.nodes)
        for node in nodes:
            node.meta.pop("creation_timestamp", None)

        grad_enabled = torch.is_grad_enabled()
        for node1, node2 in itertools.pairwise(nodes):
            if (
                node1.target is torch._C._set_grad_enabled
                and tuple(node1.args) == (not grad_enabled,)
                and not node1._erased
            ):
                grad_enabled = node1.args[0]
                if (
                    node2.target is torch._C._set_grad_enabled
                    and tuple(node2.args) == (not grad_enabled,)
                    and not node2._erased
                ):
                    grad_enabled = node2.args[0]
                    self.graph.erase_node(node1)
                    self.graph.erase_node(node2)