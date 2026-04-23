def validate_agent_executor_blocks(
        self,
        agent: AgentDict,
        library_agents: list[dict[str, Any]] | None = None,
    ) -> bool:
        """
        Validate AgentExecutorBlock nodes have required fields and valid
        references.

        Checks that AgentExecutorBlock nodes:
        1. Have a valid graph_id in input_default (required)
        2. If graph_id matches a known library agent, validates version
           consistency
        3. Sub-agent required inputs are connected via links (not hardcoded)

        Note: Unknown graph_ids are not treated as errors - they could be valid
        direct references to agents by their actual ID (not via library_agents).
        This is consistent with fix_agent_executor_blocks() behavior.

        Args:
            agent: The agent dictionary to validate
            library_agents: List of available library agents (for version
                            validation)

        Returns:
            True if all AgentExecutorBlock nodes are valid, False otherwise
        """
        valid = True
        nodes = agent.get("nodes", [])
        links = agent.get("links", [])

        # Create lookup for library agents
        library_agent_lookup: dict[str, dict[str, Any]] = {}
        if library_agents:
            library_agent_lookup = {la.get("graph_id", ""): la for la in library_agents}

        for node in nodes:
            if node.get("block_id") != AGENT_EXECUTOR_BLOCK_ID:
                continue

            node_id = node.get("id")
            input_default = node.get("input_default", {})

            # Check for required graph_id
            graph_id = input_default.get("graph_id")
            if not graph_id:
                self.add_error(
                    f"AgentExecutorBlock node '{node_id}' is missing "
                    f"required 'graph_id' in input_default. This field "
                    f"must reference the ID of the sub-agent to execute."
                )
                valid = False
                continue

            # If graph_id is not in library_agent_lookup, skip validation
            if graph_id not in library_agent_lookup:
                continue

            # Validate version consistency for known library agents
            library_agent = library_agent_lookup[graph_id]
            expected_version = library_agent.get("graph_version")
            current_version = input_default.get("graph_version")
            if (
                current_version
                and expected_version
                and current_version != expected_version
            ):
                self.add_error(
                    f"AgentExecutorBlock node '{node_id}' has mismatched "
                    f"graph_version: got {current_version}, expected "
                    f"{expected_version} for library agent "
                    f"'{library_agent.get('name')}'"
                )
                valid = False

            # Validate sub-agent inputs are properly linked (not hardcoded)
            sub_agent_input_schema = library_agent.get("input_schema", {})
            if not isinstance(sub_agent_input_schema, dict):
                sub_agent_input_schema = {}
            sub_agent_required_inputs = sub_agent_input_schema.get("required", [])
            sub_agent_properties = sub_agent_input_schema.get("properties", {})

            # Get all linked inputs to this node
            linked_sub_agent_inputs: set[str] = set()
            for link in links:
                if link.get("sink_id") == node_id:
                    sink_name = link.get("sink_name", "")
                    if sink_name in sub_agent_properties:
                        linked_sub_agent_inputs.add(sink_name)

            # Check for hardcoded inputs that should be linked
            hardcoded_inputs = input_default.get("inputs", {})
            input_schema = input_default.get("input_schema", {})
            schema_properties = (
                input_schema.get("properties", {})
                if isinstance(input_schema, dict)
                else {}
            )
            if isinstance(hardcoded_inputs, dict) and hardcoded_inputs:
                for input_name, value in hardcoded_inputs.items():
                    if input_name not in sub_agent_properties:
                        continue
                    if value is None:
                        continue
                    # Skip if this input is already linked
                    if input_name in linked_sub_agent_inputs:
                        continue
                    prop_schema = schema_properties.get(input_name, {})
                    schema_default = (
                        prop_schema.get("default")
                        if isinstance(prop_schema, dict)
                        else None
                    )
                    if schema_default is not None and self._values_equal(
                        value, schema_default
                    ):
                        continue
                    # This is a non-default hardcoded value without a link
                    self.add_error(
                        f"AgentExecutorBlock node '{node_id}' has "
                        f"hardcoded input '{input_name}'. Sub-agent "
                        f"inputs should be connected via links using "
                        f"'{input_name}' as sink_name, not hardcoded "
                        f"in input_default.inputs. Create a link from "
                        f"the appropriate source node."
                    )
                    valid = False

            # Check for missing required sub-agent inputs.
            # An input is satisfied if it is linked OR has an allowed
            # hardcoded value (i.e. equals the schema default — the
            # previous check already flags non-default hardcoded values).
            hardcoded_inputs_dict = (
                hardcoded_inputs if isinstance(hardcoded_inputs, dict) else {}
            )
            for req_input in sub_agent_required_inputs:
                if req_input in linked_sub_agent_inputs:
                    continue
                # Check if fixer populated it with a schema default value
                if req_input in hardcoded_inputs_dict:
                    prop_schema = schema_properties.get(req_input, {})
                    schema_default = (
                        prop_schema.get("default")
                        if isinstance(prop_schema, dict)
                        else None
                    )
                    if schema_default is not None and self._values_equal(
                        hardcoded_inputs_dict[req_input], schema_default
                    ):
                        continue
                self.add_error(
                    f"AgentExecutorBlock node '{node_id}' is "
                    f"missing required sub-agent input "
                    f"'{req_input}'. Create a link to this node "
                    f"using sink_name '{req_input}' to connect "
                    f"the input."
                )
                valid = False

        return valid