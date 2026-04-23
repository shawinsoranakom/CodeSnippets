def validate_sink_input_existence(
        self,
        agent: AgentDict,
        blocks: list[dict[str, Any]],
        node_lookup: dict[str, dict[str, Any]] | None = None,
    ) -> bool:
        """
        Validate that all sink_names in links and input_default keys in nodes
        exist in the corresponding block's input schema.

        Checks that for each link the sink_name references a valid input
        property in the sink block's inputSchema, and that every key in a
        node's input_default is a recognised input property. Also handles
        nested inputs with _#_ notation and dynamic schemas for
        AgentExecutorBlock.

        Args:
            agent: The agent dictionary to validate
            blocks: List of available blocks with their schemas
            node_lookup: Optional pre-built node-id → node dict

        Returns:
            True if all sink input fields exist, False otherwise
        """
        valid = True

        block_input_schemas = {
            block.get("id", ""): block.get("inputSchema", {}).get("properties", {})
            for block in blocks
        }
        block_names = {
            block.get("id", ""): block.get("name", "Unknown Block") for block in blocks
        }
        if node_lookup is None:
            node_lookup = self._build_node_lookup(agent)

        def get_input_props(node: dict[str, Any]) -> dict[str, Any]:
            block_id = node.get("block_id", "")
            if block_id == AGENT_EXECUTOR_BLOCK_ID:
                input_default = node.get("input_default", {})
                dynamic_input_schema = input_default.get("input_schema", {})
                if not isinstance(dynamic_input_schema, dict):
                    dynamic_input_schema = {}
                dynamic_props = dynamic_input_schema.get("properties", {})
                if not isinstance(dynamic_props, dict):
                    dynamic_props = {}
                static_props = block_input_schemas.get(block_id, {})
                return {**static_props, **dynamic_props}
            return block_input_schemas.get(block_id, {})

        def check_nested_input(
            input_props: dict[str, Any],
            field_name: str,
            context: str,
            block_name: str,
            block_id: str,
        ) -> bool:
            parent, child = field_name.split(DICT_SPLIT, 1)
            parent_schema = input_props.get(parent)
            if not parent_schema:
                self.add_error(
                    f"{context}: Parent property '{parent}' does not "
                    f"exist in block '{block_name}' ({block_id}) input "
                    f"schema."
                )
                return False

            allows_additional = parent_schema.get("additionalProperties", False)
            # Only anyOf is checked here because Pydantic's JSON schema
            # emits optional/union fields via anyOf. allOf and oneOf are
            # not currently used by any block's dict-typed inputs, so
            # false positives from them are not a concern in practice.
            if not allows_additional and "anyOf" in parent_schema:
                for schema_option in parent_schema.get("anyOf", []):
                    if not isinstance(schema_option, dict):
                        continue
                    if schema_option.get("additionalProperties"):
                        allows_additional = True
                        break
                    items_schema = schema_option.get("items")
                    if isinstance(items_schema, dict) and items_schema.get(
                        "additionalProperties"
                    ):
                        allows_additional = True
                        break

            if not allows_additional:
                if not (
                    isinstance(parent_schema, dict)
                    and "properties" in parent_schema
                    and isinstance(parent_schema["properties"], dict)
                    and child in parent_schema["properties"]
                ):
                    available = (
                        list(parent_schema.get("properties", {}).keys())
                        if isinstance(parent_schema, dict)
                        else []
                    )
                    self.add_error(
                        f"{context}: Child property '{child}' does not "
                        f"exist in parent '{parent}' of block "
                        f"'{block_name}' ({block_id}) input schema. "
                        f"Available properties: {available}"
                    )
                    return False
            return True

        for link in agent.get("links", []):
            sink_id = link.get("sink_id")
            sink_name = link.get("sink_name", "")
            link_id = link.get("id", "Unknown")

            if not sink_name:
                # Missing sink_name is caught by validate_data_type_compatibility
                continue

            sink_node = node_lookup.get(sink_id)
            if not sink_node:
                # Already caught by validate_link_node_references
                continue

            block_id = sink_node.get("block_id", "")
            block_name = block_names.get(block_id, "Unknown Block")
            input_props = get_input_props(sink_node)

            context = (
                f"Invalid sink input field '{sink_name}' in link "
                f"'{link_id}' to node '{sink_id}'"
            )

            if DICT_SPLIT in sink_name:
                if not check_nested_input(
                    input_props, sink_name, context, block_name, block_id
                ):
                    valid = False
            else:
                if sink_name not in input_props:
                    available_inputs = list(input_props.keys())
                    self.add_error(
                        f"{context} (block '{block_name}' - {block_id}): "
                        f"Input property '{sink_name}' does not exist in "
                        f"the block's input schema. "
                        f"Available inputs: {available_inputs}"
                    )
                    valid = False

        for node in agent.get("nodes", []):
            node_id = node.get("id")
            block_id = node.get("block_id", "")
            block_name = block_names.get(block_id, "Unknown Block")
            input_default = node.get("input_default", {})

            if not isinstance(input_default, dict) or not input_default:
                continue

            if (
                block_id not in block_input_schemas
                and block_id != AGENT_EXECUTOR_BLOCK_ID
            ):
                continue

            input_props = get_input_props(node)

            for key in input_default:
                if key == "credentials":
                    continue

                context = (
                    f"Node '{node_id}' (block '{block_name}' - {block_id}) "
                    f"has unknown input_default key '{key}'"
                )

                if DICT_SPLIT in key:
                    if not check_nested_input(
                        input_props, key, context, block_name, block_id
                    ):
                        valid = False
                else:
                    if key not in input_props:
                        available_inputs = list(input_props.keys())
                        self.add_error(
                            f"{context} which does not exist in the "
                            f"block's input schema. "
                            f"Available inputs: {available_inputs}"
                        )
                        valid = False

        return valid