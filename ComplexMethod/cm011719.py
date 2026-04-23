def _topological_sort_nodes(self) -> list[list[BaseSchedulerNode]]:
        """
        Sort nodes by their topological order, return a list of node lists.
        """
        order = []
        nodes = dict.fromkeys(self.nodes, 0)
        children: dict[Any, Any] = {}
        for node in self.nodes:
            deps = self._get_unmet_dep_nodes(node)
            nodes[node] = len(deps)
            for dep in deps:
                c = children.get(dep, [])
                c.append(node)
                children[dep] = c

        zero_deg_nodes = [n for n, v in nodes.items() if v == 0]
        while zero_deg_nodes:
            order.append(zero_deg_nodes)
            for n in zero_deg_nodes:
                for user in children.get(n, []):
                    nodes[user] -= 1
                nodes.pop(n)
            zero_deg_nodes = [n for n, v in nodes.items() if v == 0]
        assert not nodes, "Topological sort failed!"
        return order