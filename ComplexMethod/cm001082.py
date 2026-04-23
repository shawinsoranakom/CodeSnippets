def validate_required_inputs(
        self, agent: AgentDict, blocks: list[dict[str, Any]]
    ) -> bool:
        """
        Validate that all required inputs are provided for each node.
        Returns True if all required inputs are satisfied, False otherwise.
        """
        valid = True

        block_lookup = {b.get("id", ""): b for b in blocks}

        for node in agent.get("nodes", []):
            block_id = node.get("block_id")
            block = block_lookup.get(block_id)

            if not block:
                continue

            required_inputs = block.get("inputSchema", {}).get("required", [])
            input_defaults = node.get("input_default", {})
            node_id = node.get("id")

            linked_inputs = set(
                link.get("sink_name")
                for link in agent.get("links", [])
                if link.get("sink_id") == node_id and link.get("sink_name")
            )

            for req_input in required_inputs:
                if (
                    req_input not in input_defaults
                    and req_input not in linked_inputs
                    and req_input != "credentials"
                ):
                    block_name = block.get("name", "Unknown Block")
                    self.add_error(
                        f"Node '{node_id}' (block '{block_name}' - "
                        f"{block_id}) is missing required input "
                        f"'{req_input}'. This input must be either "
                        f"provided as a default value in the node's "
                        f"'input_default' field or connected via a link "
                        f"from another node's output."
                    )
                    valid = False

        return valid