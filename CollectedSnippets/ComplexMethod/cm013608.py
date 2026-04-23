def extend_acc_subgraph(self, tag: str) -> None:
        """
        Extend the acc subgraph with `tag` going the reversed topological direction.
        """
        # Dict that maps node to its users and ignore users that
        # are in the subgraph that has greater tag
        deps = self.find_reverse_deps(tag_id=int(tag.rsplit("_", maxsplit=1)[-1]))
        self.update_reverse_deps_for_fusions(deps)

        # Parent nodes of the subgraph
        parent_nodes = self.find_parent_nodes_of_subgraph(tag)

        visited_nodes: NodeSet = set()

        while parent_nodes:
            node = None

            # Find a acc node that depends on visited nodes only
            for n in parent_nodes:
                if deps[n] <= visited_nodes and n in self.acc_nodes:
                    node = n
                    break

            if node is None:
                break

            # Put the node into `tag` subgraph
            node.tag = tag  # type: ignore[attr-defined]
            parent_nodes.remove(node)
            visited_nodes.add(node)

            # If node is in a fusion group, add all fusion buddies to parent nodes
            if node in self.fusions:
                for fusion_node in self.fusions[node]:
                    if fusion_node not in visited_nodes:
                        parent_nodes.add(fusion_node)

            # Add inputs of the node to parent nodes
            for arg in node.all_input_nodes:
                if arg.op in CALLABLE_NODE_OPS and arg not in visited_nodes:
                    parent_nodes.add(arg)