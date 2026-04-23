def fix_data_type_mismatch(
        self, agent: AgentDict, blocks: list[dict[str, Any]]
    ) -> AgentDict:
        """
        Fix data type mismatches by inserting UniversalTypeConverterBlock between
        incompatible connections.

        This function:
        1. Identifies links with type mismatches using the same logic as
           validate_data_type_compatibility
        2. Inserts UniversalTypeConverterBlock nodes to convert data types
        3. Rewires the connections to go through the converter block

        Args:
            agent: The agent dictionary to fix
            blocks: List of available blocks for reference

        Returns:
            The fixed agent dictionary
        """
        nodes = agent.get("nodes", [])
        links = agent.get("links", [])

        block_lookup = {block.get("id", ""): block for block in blocks}
        node_lookup = {node.get("id", ""): node for node in nodes}

        def get_target_type_for_conversion(sink_type: str) -> str:
            """Determine the target type for conversion based on sink
            requirements."""
            type_mapping = {
                "string": "string",
                "text": "string",
                "integer": "number",
                "number": "number",
                "float": "number",
                "boolean": "boolean",
                "bool": "boolean",
                "array": "list",
                "list": "list",
                "object": "dictionary",
                "dict": "dictionary",
                "dictionary": "dictionary",
            }
            return type_mapping.get(sink_type, sink_type)

        new_links: list[dict[str, Any]] = []
        nodes_to_add: list[dict[str, Any]] = []
        converter_counter = 0

        for link in links:
            source_node = node_lookup.get(link.get("source_id"))
            sink_node = node_lookup.get(link.get("sink_id"))

            if not source_node or not sink_node:
                new_links.append(link)
                continue

            source_block = block_lookup.get(source_node.get("block_id"))
            sink_block = block_lookup.get(sink_node.get("block_id"))

            if not source_block or not sink_block:
                new_links.append(link)
                continue

            source_outputs = source_block.get("outputSchema", {}).get("properties", {})
            sink_inputs = sink_block.get("inputSchema", {}).get("properties", {})

            source_type = get_defined_property_type(
                source_outputs, link.get("source_name", "")
            )
            sink_type = get_defined_property_type(
                sink_inputs, link.get("sink_name", "")
            )

            # Check if types are incompatible
            if (
                source_type
                and sink_type
                and not are_types_compatible(source_type, sink_type)
            ):
                # Create UniversalTypeConverterBlock node
                converter_node_id = generate_uuid()
                target_type = get_target_type_for_conversion(sink_type)

                converter_node = {
                    "id": converter_node_id,
                    "block_id": _UNIVERSAL_TYPE_CONVERTER_BLOCK_ID,
                    "input_default": {"type": target_type},
                    "metadata": {
                        "position": {
                            "x": converter_counter * 250,
                            "y": 100,
                        }
                    },
                    "graph_id": agent.get("id"),
                    "graph_version": 1,
                }
                nodes_to_add.append(converter_node)
                converter_counter += 1

                # Create new links: source -> converter -> sink
                source_to_converter_link = {
                    "id": generate_uuid(),
                    "source_id": link.get("source_id", ""),
                    "source_name": link.get("source_name", ""),
                    "sink_id": converter_node_id,
                    "sink_name": "value",
                }

                converter_to_sink_link = {
                    "id": generate_uuid(),
                    "source_id": converter_node_id,
                    "source_name": "value",
                    "sink_id": link.get("sink_id", ""),
                    "sink_name": link.get("sink_name", ""),
                }

                new_links.append(source_to_converter_link)
                new_links.append(converter_to_sink_link)

                source_block_name = source_block.get("name", "Unknown Block")
                sink_block_name = sink_block.get("name", "Unknown Block")
                self.add_fix_log(
                    f"Fixed data type mismatch: Inserted "
                    f"UniversalTypeConverterBlock {converter_node_id} "
                    f"between {source_block_name} ({source_type}) and "
                    f"{sink_block_name} ({sink_type}) converting to "
                    f"{target_type}"
                )
            else:
                # Keep the original link if types are compatible
                new_links.append(link)

        # Update the agent with new nodes and links
        if nodes_to_add:
            nodes.extend(nodes_to_add)
            agent["nodes"] = nodes
            agent["links"] = new_links

        return agent