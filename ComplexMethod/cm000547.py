async def _create_agent_function_signature(
        sink_node: "Node", links: list["Link"]
    ) -> dict[str, Any]:
        """
        Creates a function signature for an agent node.

        Args:
            sink_node: The agent node for which to create a function signature.
            links: The list of links connected to the sink node.

        Returns:
            A dictionary representing the function signature in the format expected by LLM tools.

        Raises:
            ValueError: If the graph metadata for the specified graph_id and graph_version is not found.
        """
        graph_id = sink_node.input_default.get("graph_id")
        graph_version = sink_node.input_default.get("graph_version")
        if not graph_id or not graph_version:
            raise ValueError("Graph ID or Graph Version not found in sink node.")

        db_client = get_database_manager_async_client()
        sink_graph_meta = await db_client.get_graph_metadata(graph_id, graph_version)
        if not sink_graph_meta:
            raise ValueError(
                f"Sink graph metadata not found: {graph_id} {graph_version}"
            )

        # Use custom name from node metadata if set, otherwise fall back to graph name
        custom_name = sink_node.metadata.get("customized_name")
        tool_name = custom_name if custom_name else sink_graph_meta.name

        tool_function: dict[str, Any] = {
            "name": OrchestratorBlock.cleanup(tool_name),
            "description": sink_graph_meta.description,
        }

        properties = {}
        field_mapping = {}

        for link in links:
            field_name = link.sink_name

            clean_field_name = OrchestratorBlock.cleanup(field_name)
            field_mapping[clean_field_name] = field_name

            sink_block_input_schema = sink_node.input_default["input_schema"]
            sink_block_properties = sink_block_input_schema.get("properties", {}).get(
                link.sink_name, {}
            )
            description = (
                sink_block_properties["description"]
                if "description" in sink_block_properties
                else f"The {link.sink_name} of the tool"
            )
            properties[clean_field_name] = {
                "type": "string",
                "description": description,
                "default": json.dumps(sink_block_properties.get("default", None)),
            }

        tool_function["parameters"] = {
            "type": "object",
            "properties": properties,
            "additionalProperties": False,
            "strict": True,
        }

        tool_function["_field_mapping"] = field_mapping
        tool_function["_sink_node_id"] = sink_node.id

        # Store hardcoded defaults (non-linked inputs) for disambiguation.
        # Exclude linked fields, private fields, agent meta fields, and
        # credential/auth fields to avoid leaking sensitive data.
        linked_fields = {link.sink_name for link in links}
        defaults = sink_node.input_default
        tool_function["_hardcoded_defaults"] = (
            {
                k: v
                for k, v in defaults.items()
                if k not in linked_fields
                and k not in ("graph_id", "graph_version", "input_schema")
                and not k.startswith("_")
                and k.lower() not in SENSITIVE_FIELD_NAMES
            }
            if isinstance(defaults, dict)
            else {}
        )

        return {"type": "function", "function": tool_function}