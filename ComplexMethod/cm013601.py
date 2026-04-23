def recursive_add_node(
        self,
        fusion_group: "FxNetAccFusionsFinder.FusionGroup",
        inputs: NodeSet | NodeList,
        visited: NodeSet | None = None,
    ) -> bool:
        """
        Start from inputs and going reverse topological order. If any upstream node
        is in the fusion group, add all the nodes in this path to fusion group.
        """
        for arg in inputs:
            # skip the node if already seen
            if visited is not None:
                if arg in visited:
                    continue
                visited.add(arg)

            # Skip placeholder and get_attr because they won't be in the fusion group.
            if arg.op not in CALLABLE_NODE_OPS:
                continue

            # If the node has smaller idx, it's already an upstream node of the fusion
            # group. We don't need to check it anymore.
            if self.node_index[arg] < fusion_group.top_node_idx:
                continue

            # If the node is in the fusion group, return True.
            if arg in fusion_group.nodes:
                return True

            # Check the upstream nodes of the node, if any of them is in the fusion group
            # we'll add this node to fusion group and return True.
            if self.recursive_add_node(fusion_group, arg.all_input_nodes, visited):
                fusion_group.add_node(arg)
                return True

        return False