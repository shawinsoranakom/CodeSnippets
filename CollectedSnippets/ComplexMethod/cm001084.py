def validate_source_output_existence(
        self,
        agent: AgentDict,
        blocks: list[dict[str, Any]],
        node_lookup: dict[str, dict[str, Any]] | None = None,
    ) -> bool:
        """
        Validate that all source_names in links exist in the corresponding
        block's output schema.

        Checks that for each link, the source_name field references a valid
        output property in the source block's outputSchema. Also handles nested
        outputs with _#_ notation.

        Args:
            agent: The agent dictionary to validate
            blocks: List of available blocks with their schemas
            node_lookup: Optional pre-built node-id → node dict

        Returns:
            True if all source output fields exist, False otherwise
        """
        valid = True

        # Create lookup dictionaries for efficiency
        block_output_schemas = {
            block.get("id", ""): block.get("outputSchema", {}).get("properties", {})
            for block in blocks
        }
        block_names = {
            block.get("id", ""): block.get("name", "Unknown Block") for block in blocks
        }
        if node_lookup is None:
            node_lookup = self._build_node_lookup(agent)

        for link in agent.get("links", []):
            source_id = link.get("source_id")
            source_name = link.get("source_name", "")
            link_id = link.get("id", "Unknown")

            if not source_name:
                self.add_error(
                    f"Link '{link_id}' is missing 'source_name'. "
                    f"Every link must specify which output field to read from."
                )
                valid = False
                continue

            source_node = node_lookup.get(source_id)
            if not source_node:
                # This error is already caught by
                # validate_link_node_references
                continue

            block_id = source_node.get("block_id")
            block_name = block_names.get(block_id, "Unknown Block")

            # Special handling for AgentExecutorBlock - use dynamic
            # output_schema from input_default
            if block_id == AGENT_EXECUTOR_BLOCK_ID:
                input_default = source_node.get("input_default", {})
                dynamic_output_schema = input_default.get("output_schema", {})
                if not isinstance(dynamic_output_schema, dict):
                    dynamic_output_schema = {}
                output_props = dynamic_output_schema.get("properties", {})
                if not isinstance(output_props, dict):
                    output_props = {}
            else:
                output_props = block_output_schemas.get(block_id, {})

            # Handle nested source names (with _#_ notation)
            if DICT_SPLIT in source_name:
                parent, child = source_name.split(DICT_SPLIT, 1)

                parent_schema = output_props.get(parent)
                if not parent_schema:
                    self.add_error(
                        f"Invalid source output field '{source_name}' "
                        f"in link '{link_id}' from node '{source_id}' "
                        f"(block '{block_name}' - {block_id}): Parent "
                        f"property '{parent}' does not exist in the "
                        f"block's output schema."
                    )
                    valid = False
                    continue

                # Check if additionalProperties is allowed either directly
                # or via anyOf
                allows_additional_properties = parent_schema.get(
                    "additionalProperties", False
                )
                if not allows_additional_properties and "anyOf" in parent_schema:
                    any_of_schemas = parent_schema.get("anyOf", [])
                    if isinstance(any_of_schemas, list):
                        for schema_option in any_of_schemas:
                            if isinstance(schema_option, dict) and schema_option.get(
                                "additionalProperties"
                            ):
                                allows_additional_properties = True
                                break
                            # Also allow when items have
                            # additionalProperties (array of objects)
                            if (
                                isinstance(schema_option, dict)
                                and "items" in schema_option
                            ):
                                items_schema = schema_option.get("items")
                                if isinstance(items_schema, dict) and items_schema.get(
                                    "additionalProperties"
                                ):
                                    allows_additional_properties = True
                                    break

                # Only require child in properties when
                # additionalProperties is not allowed
                if not allows_additional_properties:
                    if not (
                        isinstance(parent_schema, dict)
                        and "properties" in parent_schema
                        and isinstance(parent_schema["properties"], dict)
                        and child in parent_schema["properties"]
                    ):
                        available_props = (
                            list(parent_schema.get("properties", {}).keys())
                            if isinstance(parent_schema, dict)
                            else []
                        )
                        self.add_error(
                            f"Invalid nested source output field "
                            f"'{source_name}' in link '{link_id}' from "
                            f"node '{source_id}' (block "
                            f"'{block_name}' - {block_id}): Child "
                            f"property '{child}' does not exist in "
                            f"parent '{parent}' output schema. "
                            f"Available properties: {available_props}"
                        )
                        valid = False
            else:
                # Check simple (non-nested) source name
                if source_name not in output_props:
                    available_outputs = list(output_props.keys())
                    self.add_error(
                        f"Invalid source output field '{source_name}' "
                        f"in link '{link_id}' from node '{source_id}' "
                        f"(block '{block_name}' - {block_id}): Output "
                        f"property '{source_name}' does not exist in "
                        f"the block's output schema. Available outputs: "
                        f"{available_outputs}"
                    )
                    valid = False

        return valid