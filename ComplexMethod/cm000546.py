async def _create_block_function_signature(
        sink_node: "Node", links: list["Link"]
    ) -> dict[str, Any]:
        """
        Creates a function signature for a block node.

        Args:
            sink_node: The node for which to create a function signature.
            links: The list of links connected to the sink node.

        Returns:
            A dictionary representing the function signature in the format expected by LLM tools.

        Raises:
            ValueError: If the block specified by sink_node.block_id is not found.
        """
        block = sink_node.block

        # Use custom name from node metadata if set, otherwise fall back to block.name
        custom_name = sink_node.metadata.get("customized_name")
        tool_name = custom_name if custom_name else block.name

        tool_function: dict[str, Any] = {
            "name": OrchestratorBlock.cleanup(tool_name),
            "description": block.description,
        }
        sink_block_input_schema = block.input_schema
        properties = {}
        field_mapping = {}  # clean_name -> original_name

        for link in links:
            field_name = link.sink_name
            is_dynamic = is_dynamic_field(field_name)
            # Clean property key to ensure Anthropic API compatibility for ALL fields
            clean_field_name = OrchestratorBlock.cleanup(field_name)
            field_mapping[clean_field_name] = field_name

            if is_dynamic:
                # For dynamic fields, use cleaned name but preserve original in description
                properties[clean_field_name] = {
                    "type": "string",
                    "description": get_dynamic_field_description(field_name),
                }
            else:
                # For regular fields, use the block's schema directly
                try:
                    properties[clean_field_name] = (
                        sink_block_input_schema.get_field_schema(field_name)
                    )
                except (KeyError, AttributeError):
                    # If field doesn't exist in schema, provide a generic one
                    properties[clean_field_name] = {
                        "type": "string",
                        "description": f"Value for {field_name}",
                    }

        # Build the parameters schema using a single unified path
        base_schema = block.input_schema.jsonschema()
        base_required = set(base_schema.get("required", []))

        # Compute required fields at the leaf level:
        # - If a linked field is dynamic and its base is required in the block schema, require the leaf
        # - If a linked field is regular and is required in the block schema, require the leaf
        required_fields: set[str] = set()
        for link in links:
            field_name = link.sink_name
            is_dynamic = is_dynamic_field(field_name)
            # Always use cleaned field name for property key (Anthropic API compliance)
            clean_field_name = OrchestratorBlock.cleanup(field_name)

            if is_dynamic:
                base_name = extract_base_field_name(field_name)
                if base_name in base_required:
                    required_fields.add(clean_field_name)
            else:
                if field_name in base_required:
                    required_fields.add(clean_field_name)

        tool_function["parameters"] = {
            "type": "object",
            "properties": properties,
            "additionalProperties": False,
            "required": sorted(required_fields),
        }

        # Store field mapping and node info for later use in output processing
        tool_function["_field_mapping"] = field_mapping
        tool_function["_sink_node_id"] = sink_node.id

        # Store hardcoded defaults (non-linked inputs) for disambiguation.
        # Exclude linked fields, private fields, and credential/auth fields
        # to avoid leaking sensitive data into tool descriptions.
        linked_fields = {link.sink_name for link in links}
        defaults = sink_node.input_default
        tool_function["_hardcoded_defaults"] = (
            {
                k: v
                for k, v in defaults.items()
                if k not in linked_fields
                and not k.startswith("_")
                and k.lower() not in SENSITIVE_FIELD_NAMES
            }
            if isinstance(defaults, dict)
            else {}
        )

        return {"type": "function", "function": tool_function}