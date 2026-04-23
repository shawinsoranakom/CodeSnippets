def validate_data_type_compatibility(
        self,
        agent: AgentDict,
        blocks: list[dict[str, Any]],
        node_lookup: dict[str, dict[str, Any]] | None = None,
    ) -> bool:
        """
        Validate that linked data types are compatible between source and sink.
        Returns True if all data types are compatible, False otherwise.
        """
        valid = True
        if node_lookup is None:
            node_lookup = self._build_node_lookup(agent)
        block_lookup = {block.get("id", ""): block for block in blocks}

        for link in agent.get("links", []):
            source_id = link.get("source_id")
            sink_id = link.get("sink_id")
            source_name = link.get("source_name")
            sink_name = link.get("sink_name")

            if not all(
                isinstance(v, str) and v
                for v in (source_id, sink_id, source_name, sink_name)
            ):
                self.add_error(
                    f"Link '{link.get('id', 'Unknown')}' is missing required "
                    f"fields (source_id/sink_id/source_name/sink_name)."
                )
                valid = False
                continue

            source_node = node_lookup.get(source_id)
            sink_node = node_lookup.get(sink_id)

            if not source_node or not sink_node:
                continue

            source_block = block_lookup.get(source_node.get("block_id", ""))
            sink_block = block_lookup.get(sink_node.get("block_id", ""))

            if not source_block or not sink_block:
                continue

            source_outputs = source_block.get("outputSchema", {}).get("properties", {})
            sink_inputs = sink_block.get("inputSchema", {}).get("properties", {})

            source_type = get_defined_property_type(source_outputs, source_name)
            sink_type = get_defined_property_type(sink_inputs, sink_name)

            if (
                source_type
                and sink_type
                and not are_types_compatible(source_type, sink_type)
            ):
                source_block_name = source_block.get("name", "Unknown Block")
                sink_block_name = sink_block.get("name", "Unknown Block")
                self.add_error(
                    f"Data type mismatch in link '{link.get('id')}': "
                    f"Source '{source_block_name}' output "
                    f"'{link.get('source_name', '')}' outputs '{source_type}' "
                    f"type, but sink '{sink_block_name}' input "
                    f"'{link.get('sink_name', '')}' expects '{sink_type}' type. "
                    f"These types must match for the connection to work "
                    f"properly."
                )
                valid = False

        return valid