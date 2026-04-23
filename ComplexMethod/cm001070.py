def fix_mcp_tool_blocks(self, agent: AgentDict) -> AgentDict:
        """Fix MCPToolBlock nodes to ensure they have required fields.

        Ensures:
        1. `tool_arguments` is present (defaults to `{}`)
        2. `tool_input_schema` is present (defaults to `{}`)
        3. `tool_arguments` is populated with default/null values from
           `tool_input_schema` properties (matching AgentExecutorBlock pattern)

        Args:
            agent: The agent dictionary to fix

        Returns:
            The fixed agent dictionary
        """
        nodes = agent.get("nodes", [])

        for node in nodes:
            if node.get("block_id") != MCP_TOOL_BLOCK_ID:
                continue

            node_id = node.get("id", "unknown")
            input_default = node.setdefault("input_default", {})

            if "tool_input_schema" not in input_default:
                input_default["tool_input_schema"] = {}
                self.add_fix_log(
                    f"MCPToolBlock {node_id}: Added missing tool_input_schema"
                )

            if "tool_arguments" not in input_default:
                input_default["tool_arguments"] = {}
                self.add_fix_log(
                    f"MCPToolBlock {node_id}: Added missing tool_arguments"
                )

            # Populate tool_arguments with defaults from tool_input_schema
            tool_schema = input_default.get("tool_input_schema", {})
            schema_properties = (
                tool_schema.get("properties", {})
                if isinstance(tool_schema, dict)
                else {}
            )
            tool_args = input_default.get("tool_arguments", {})
            if isinstance(schema_properties, dict) and isinstance(tool_args, dict):
                for prop_name, prop_schema in schema_properties.items():
                    if prop_name not in tool_args and isinstance(prop_schema, dict):
                        default_value = prop_schema.get("default")
                        tool_args[prop_name] = default_value
                        self.add_fix_log(
                            f"MCPToolBlock {node_id}: Added default value "
                            f"for tool argument '{prop_name}'"
                        )

        return agent