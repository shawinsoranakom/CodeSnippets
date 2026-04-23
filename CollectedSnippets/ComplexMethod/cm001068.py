def fix_agent_executor_blocks(
        self,
        agent: AgentDict,
        library_agents: list[dict[str, Any]] | None = None,
    ) -> AgentDict:
        """
        Fix AgentExecutorBlock nodes to ensure they have valid graph_id
        references.

        This function:
        1. Validates that AgentExecutorBlock nodes reference valid library agents
        2. Fills in missing graph_version if graph_id is valid
        3. Ensures input_default has required fields
        4. Clears hardcoded inputs (they should be connected via links)
        5. Logs missing required input links for the LLM to fix

        Args:
            agent: The agent dictionary to fix
            library_agents: List of library agents available for composition

        Returns:
            The fixed agent dictionary
        """
        if not library_agents:
            logger.debug(
                "fix_agent_executor_blocks: No library_agents provided, skipping"
            )
            return agent

        nodes = agent.get("nodes", [])
        links = agent.get("links", [])

        # Create lookup for library agents
        library_agent_lookup = {la.get("graph_id", ""): la for la in library_agents}
        logger.debug(
            f"fix_agent_executor_blocks: library_agent_lookup keys = "
            f"{list(library_agent_lookup.keys())}"
        )

        for node in nodes:
            if node.get("block_id") != AGENT_EXECUTOR_BLOCK_ID:
                continue

            node_id = node.get("id")
            input_default = node.get("input_default", {})

            # Check if graph_id references a library agent
            graph_id = input_default.get("graph_id")
            logger.debug(
                f"fix_agent_executor_blocks: Found AgentExecutorBlock "
                f"{node_id}, graph_id={graph_id}"
            )

            if not graph_id:
                logger.warning(
                    f"fix_agent_executor_blocks: Node {node_id} has no "
                    f"graph_id, skipping"
                )
                continue

            library_agent = library_agent_lookup.get(graph_id)
            if not library_agent:
                logger.warning(
                    f"fix_agent_executor_blocks: graph_id {graph_id} not "
                    f"found in library_agents lookup"
                )
                continue

            logger.debug(
                f"fix_agent_executor_blocks: Found matching library agent "
                f"'{library_agent.get('name')}', input_schema keys: "
                f"{list(library_agent.get('input_schema', {}).get('properties', {}).keys())}"
            )

            # Fill in graph_version if missing or mismatched
            expected_version = library_agent.get("graph_version")
            current_version = input_default.get("graph_version")

            if current_version != expected_version:
                input_default["graph_version"] = expected_version
                self.add_fix_log(
                    f"Fixed AgentExecutorBlock {node_id}: "
                    f"graph_version {current_version} -> {expected_version} "
                    f"(for library agent '{library_agent.get('name')}')"
                )

            # Ensure user_id is present (can be empty string, filled at runtime)
            if "user_id" not in input_default:
                input_default["user_id"] = ""
                self.add_fix_log(
                    f"Fixed AgentExecutorBlock {node_id}: Added missing user_id"
                )

            # Ensure inputs is present
            if "inputs" not in input_default:
                input_default["inputs"] = {}

            # Ensure input_schema is present and valid (copy from library agent)
            current_input_schema = input_default.get("input_schema")
            lib_input_schema = library_agent.get("input_schema", {})
            if not isinstance(lib_input_schema, dict):
                lib_input_schema = {}
            if not isinstance(current_input_schema, dict):
                current_input_schema = {}
            logger.debug(
                f"fix_agent_executor_blocks: current_input_schema="
                f"{current_input_schema}"
            )
            logger.debug(
                f"fix_agent_executor_blocks: lib_input_schema keys="
                f"{list(lib_input_schema.get('properties', {}).keys()) if lib_input_schema else 'None'}"
            )
            if not current_input_schema or not current_input_schema.get("properties"):
                input_default["input_schema"] = lib_input_schema
                logger.debug(
                    "fix_agent_executor_blocks: Replaced input_schema "
                    "with library agent's schema"
                )
                if not current_input_schema:
                    self.add_fix_log(
                        f"Fixed AgentExecutorBlock {node_id}: Added "
                        f"missing input_schema"
                    )
                else:
                    self.add_fix_log(
                        f"Fixed AgentExecutorBlock {node_id}: Replaced "
                        f"empty input_schema with library agent's schema"
                    )

            # Populate inputs object with default values from input_schema
            # properties. This matches how the frontend creates
            # AgentExecutorBlock nodes.
            final_input_schema = input_default.get("input_schema", {})
            schema_properties = final_input_schema.get("properties", {})
            inputs_obj = input_default.get("inputs", {})
            if isinstance(schema_properties, dict) and isinstance(inputs_obj, dict):
                for prop_name, prop_schema in schema_properties.items():
                    if prop_name not in inputs_obj and isinstance(prop_schema, dict):
                        default_value = prop_schema.get("default")
                        if default_value is not None:
                            inputs_obj[prop_name] = default_value
                input_default["inputs"] = inputs_obj

            # Ensure output_schema is present and valid (copy from library
            # agent)
            current_output_schema = input_default.get("output_schema")
            lib_output_schema = library_agent.get("output_schema", {})
            if not isinstance(lib_output_schema, dict):
                lib_output_schema = {}
            if not isinstance(current_output_schema, dict):
                current_output_schema = {}
            if not current_output_schema or not current_output_schema.get("properties"):
                input_default["output_schema"] = lib_output_schema
                if not current_output_schema:
                    self.add_fix_log(
                        f"Fixed AgentExecutorBlock {node_id}: Added "
                        f"missing output_schema"
                    )
                else:
                    self.add_fix_log(
                        f"Fixed AgentExecutorBlock {node_id}: Replaced "
                        f"empty output_schema with library agent's schema"
                    )

            # Check for missing required input links and fix sink_name format
            sub_agent_input_schema = library_agent.get("input_schema", {})
            if not isinstance(sub_agent_input_schema, dict):
                sub_agent_input_schema = {}
            sub_agent_required_inputs = sub_agent_input_schema.get("required", [])

            # Get all linked inputs to this node
            sub_agent_properties = sub_agent_input_schema.get("properties", {})
            linked_sub_agent_inputs: set[str] = set()
            for link in links:
                if link.get("sink_id") == node_id:
                    sink_name = link.get("sink_name", "")
                    # Fix: Convert "inputs_#_<field>" to direct property
                    # name "<field>"
                    if sink_name.startswith("inputs_#_"):
                        prop_name = sink_name[9:]  # Remove "inputs_#_"
                        if prop_name in sub_agent_properties:
                            link["sink_name"] = prop_name
                            self.add_fix_log(
                                f"Fixed AgentExecutorBlock link: "
                                f"sink_name '{sink_name}' -> "
                                f"'{prop_name}' (removed inputs_#_ "
                                f"prefix)"
                            )
                            linked_sub_agent_inputs.add(prop_name)
                    elif sink_name in sub_agent_properties:
                        linked_sub_agent_inputs.add(sink_name)

            missing_inputs = [
                inp
                for inp in sub_agent_required_inputs
                if inp not in linked_sub_agent_inputs
            ]
            if missing_inputs:
                self.add_fix_log(
                    f"AgentExecutorBlock {node_id} (sub-agent "
                    f"'{library_agent.get('name')}') needs links for "
                    f"required inputs: {missing_inputs}."
                )

            node["input_default"] = input_default

        return agent