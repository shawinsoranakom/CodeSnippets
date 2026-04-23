def validate_orchestrator_blocks(
        self,
        agent: AgentDict,
        node_lookup: dict[str, dict[str, Any]] | None = None,
    ) -> bool:
        """Validate that OrchestratorBlock nodes have downstream tools.

        Checks that each OrchestratorBlock node has at least one link
        with ``source_name == "tools"`` connecting to a downstream block.
        Without tools, the block has nothing to call and will error at runtime.

        Returns True if all OrchestratorBlock nodes are valid.
        """
        valid = True
        nodes = agent.get("nodes", [])
        links = agent.get("links", [])
        if node_lookup is None:
            node_lookup = self._build_node_lookup(agent)
        non_tool_block_ids = {AGENT_INPUT_BLOCK_ID, AGENT_OUTPUT_BLOCK_ID}

        for node in nodes:
            if node.get("block_id") != TOOL_ORCHESTRATOR_BLOCK_ID:
                continue

            node_id = node.get("id", "unknown")
            customized_name = (node.get("metadata") or {}).get(
                "customized_name", node_id
            )

            # Warn if agent_mode_max_iterations is 0 (traditional mode) —
            # requires complex external conversation-history loop wiring
            # that the agent generator does not produce.
            input_default = node.get("input_default", {})
            max_iter = input_default.get("agent_mode_max_iterations")
            if max_iter is not None and not isinstance(max_iter, int):
                self.add_error(
                    f"OrchestratorBlock node '{customized_name}' "
                    f"({node_id}) has non-integer "
                    f"agent_mode_max_iterations={max_iter!r}. "
                    f"This field must be an integer."
                )
                valid = False
            elif isinstance(max_iter, int) and max_iter < -1:
                self.add_error(
                    f"OrchestratorBlock node '{customized_name}' "
                    f"({node_id}) has invalid "
                    f"agent_mode_max_iterations={max_iter}. "
                    f"Use -1 for infinite or a positive number for "
                    f"bounded iterations."
                )
                valid = False
            elif isinstance(max_iter, int) and max_iter > 100:
                self.add_error(
                    f"OrchestratorBlock node '{customized_name}' "
                    f"({node_id}) has agent_mode_max_iterations="
                    f"{max_iter} which is unusually high. Values above "
                    f"100 risk excessive cost and long execution times. "
                    f"Consider using a lower value (3-10) or -1 for "
                    f"genuinely open-ended tasks."
                )
                valid = False
            elif max_iter == 0:
                self.add_error(
                    f"OrchestratorBlock node '{customized_name}' "
                    f"({node_id}) has agent_mode_max_iterations=0 "
                    f"(traditional mode). The agent generator only supports "
                    f"agent mode (set to -1 for infinite or a positive "
                    f"number for bounded iterations)."
                )
                valid = False

            has_tools = any(
                link.get("source_id") == node_id
                and link.get("source_name") == "tools"
                and node_lookup.get(link.get("sink_id", ""), {}).get("block_id")
                not in non_tool_block_ids
                for link in links
            )

            if not has_tools:
                self.add_error(
                    f"OrchestratorBlock node '{customized_name}' "
                    f"({node_id}) has no downstream tool blocks connected. "
                    f"Connect at least one block to its 'tools' output so "
                    f"the AI has tools to call."
                )
                valid = False

        return valid