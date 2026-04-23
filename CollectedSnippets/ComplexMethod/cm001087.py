def validate_agent_executor_block_schemas(
        self,
        agent: AgentDict,
    ) -> bool:
        """
        Validate that AgentExecutorBlock nodes have valid input_schema and
        output_schema.

        This validation runs regardless of library_agents availability and
        ensures that the schemas are properly populated to prevent frontend
        crashes.

        Args:
            agent: The agent dictionary to validate

        Returns:
            True if all AgentExecutorBlock nodes have valid schemas, False
            otherwise
        """
        valid = True
        nodes = agent.get("nodes", [])

        for node in nodes:
            if node.get("block_id") != AGENT_EXECUTOR_BLOCK_ID:
                continue

            node_id = node.get("id")
            input_default = node.get("input_default", {})
            customized_name = (node.get("metadata") or {}).get(
                "customized_name", "Unknown"
            )

            # Check input_schema
            input_schema = input_default.get("input_schema")
            if input_schema is None or not isinstance(input_schema, dict):
                self.add_error(
                    f"AgentExecutorBlock node '{node_id}' "
                    f"({customized_name}) has missing or invalid "
                    f"input_schema. The input_schema must be a valid "
                    f"JSON Schema object with 'properties' and "
                    f"'required' fields."
                )
                valid = False
            elif not input_schema.get("properties") and not input_schema.get("type"):
                # Empty schema like {} is invalid
                self.add_error(
                    f"AgentExecutorBlock node '{node_id}' "
                    f"({customized_name}) has empty input_schema. The "
                    f"input_schema must define the sub-agent's expected "
                    f"inputs. This usually indicates the sub-agent "
                    f"reference is incomplete or the library agent was "
                    f"not properly passed."
                )
                valid = False

            # Check output_schema
            output_schema = input_default.get("output_schema")
            if output_schema is None or not isinstance(output_schema, dict):
                self.add_error(
                    f"AgentExecutorBlock node '{node_id}' "
                    f"({customized_name}) has missing or invalid "
                    f"output_schema. The output_schema must be a valid "
                    f"JSON Schema object defining the sub-agent's "
                    f"outputs."
                )
                valid = False
            elif not output_schema.get("properties") and not output_schema.get("type"):
                # Empty schema like {} is invalid
                self.add_error(
                    f"AgentExecutorBlock node '{node_id}' "
                    f"({customized_name}) has empty output_schema. "
                    f"The output_schema must define the sub-agent's "
                    f"expected outputs. This usually indicates the "
                    f"sub-agent reference is incomplete or the library "
                    f"agent was not properly passed."
                )
                valid = False

        return valid