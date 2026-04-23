def graph_validate(self) -> None:
        """Validate graph structure and execution rules."""
        if not self.nodes:
            raise ValueError("Graph has no nodes.")

        if not self.get_start_nodes():
            raise ValueError("Graph must have at least one start node")

        if not self.get_leaf_nodes():
            raise ValueError("Graph must have at least one leaf node")

        # Outgoing edge condition validation (per node)
        for node in self.nodes.values():
            # Check that if a node has an outgoing conditional edge, then all outgoing edges are conditional
            has_condition = any(
                edge.condition is not None or edge.condition_function is not None for edge in node.edges
            )
            has_unconditioned = any(edge.condition is None and edge.condition_function is None for edge in node.edges)
            if has_condition and has_unconditioned:
                raise ValueError(f"Node '{node.name}' has a mix of conditional and unconditional edges.")

        # Validate activation conditions across all edges in the graph
        self._validate_activation_conditions()

        self._has_cycles = self.has_cycles_with_exit()