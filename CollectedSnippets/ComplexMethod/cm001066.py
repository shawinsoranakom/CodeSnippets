def fix_node_x_coordinates(
        self,
        agent: AgentDict,
        node_lookup: dict[str, dict[str, Any]] | None = None,
    ) -> AgentDict:
        """
        Fix node x-coordinates to ensure adjacent nodes (connected via links)
        have at least 800 units difference in their x-coordinates.

        For each link connecting two nodes, if the x-coordinate difference is
        less than or equal to 800, the sink node's x-coordinate will be adjusted
        to be at least 800 units to the right of the source node.

        Args:
            agent: The agent dictionary to fix

        Returns:
            The fixed agent dictionary
        """
        links = agent.get("links", [])

        # Create a lookup dictionary for nodes by ID
        if node_lookup is None:
            node_lookup = self._build_node_lookup(agent)

        # Iterate through all links and adjust positions as needed
        for link in links:
            source_id = link.get("source_id")
            sink_id = link.get("sink_id")

            if not source_id or not sink_id:
                continue

            source_node = node_lookup.get(source_id)
            sink_node = node_lookup.get(sink_id)

            if not source_node or not sink_node:
                continue

            # Skip self-referencing links (e.g. AddToList feeding itself)
            if source_id == sink_id:
                continue

            source_pos = (source_node.get("metadata") or {}).get("position", {})
            sink_meta = sink_node.get("metadata") or {}
            sink_pos = sink_meta.get("position", {})
            source_x = source_pos.get("x", 0)
            sink_x = sink_pos.get("x", 0)

            difference = abs(sink_x - source_x)
            if difference < 800:
                required_x = source_x + 800
                if sink_node.get("metadata") is None:
                    sink_node["metadata"] = {}
                if sink_node["metadata"].get("position") is None:
                    sink_node["metadata"]["position"] = {}
                sink_node["metadata"]["position"]["x"] = required_x
                self.add_fix_log(
                    f"Adjusted x-coordinate for node {sink_id}: "
                    f"{sink_x} -> {required_x} (source node {source_id} "
                    f"at x={source_x}, ensuring minimum 800 unit spacing)"
                )
            else:
                continue

        return agent