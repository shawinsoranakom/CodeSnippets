def fix_invalid_nested_sink_links(
        self,
        agent: AgentDict,
        blocks: list[dict[str, Any]],
        node_lookup: dict[str, dict[str, Any]] | None = None,
    ) -> AgentDict:
        """
        Fix invalid nested sink links (links with _#_ notation pointing to
        array indices).

        The LLM sometimes generates links like 'values_#_0' for CreateListBlock,
        which is invalid because:
        1. 'values' is an array type, not an object with named properties
        2. The _#_ notation is for accessing nested object properties, not array
           indices

        This fix removes such invalid links to prevent validation errors.

        Args:
            agent: The agent dictionary to fix
            blocks: List of available blocks with their schemas

        Returns:
            The fixed agent dictionary
        """
        if not blocks:
            return agent

        block_input_schemas = {
            block.get("id", ""): block.get("inputSchema", {}).get("properties", {})
            for block in blocks
        }
        block_names = {
            block.get("id", ""): block.get("name", "Unknown Block") for block in blocks
        }

        if node_lookup is None:
            node_lookup = self._build_node_lookup(agent)

        links = agent.get("links", [])
        links_to_remove: list[str] = []

        for link in links:
            sink_name = link.get("sink_name", "")

            if DICT_SPLIT in sink_name:
                parent, child = sink_name.split(DICT_SPLIT, 1)

                # Check if child is a numeric index (invalid for _#_ notation)
                if child.isdigit():
                    sink_node = node_lookup.get(link.get("sink_id", ""))
                    if sink_node:
                        block_id = sink_node.get("block_id")
                        block_name = block_names.get(block_id, "Unknown Block")
                        self.add_fix_log(
                            f"Removing invalid nested sink link "
                            f"'{sink_name}' for block '{block_name}': "
                            f"Array indices (like '{child}') are not "
                            f"valid with _#_ notation"
                        )
                        links_to_remove.append(link.get("id", ""))
                    continue

                # Check if parent property exists and child is valid
                sink_node = node_lookup.get(link.get("sink_id", ""))
                if sink_node:
                    block_id = sink_node.get("block_id")
                    input_props = block_input_schemas.get(block_id, {})
                    parent_schema = input_props.get(parent)

                    # If parent doesn't exist or is an array type, remove
                    if parent_schema:
                        parent_type = parent_schema.get("type")
                        if parent_type == "array":
                            block_name = block_names.get(block_id, "Unknown Block")
                            self.add_fix_log(
                                f"Removing invalid nested sink link "
                                f"'{sink_name}' for block "
                                f"'{block_name}': '{parent}' is an "
                                f"array type, _#_ notation not "
                                f"applicable"
                            )
                            links_to_remove.append(link.get("id", ""))

        # Remove invalid links
        if links_to_remove:
            agent["links"] = [
                link for link in links if link.get("id", "") not in links_to_remove
            ]

        return agent