async def _create_tool_node_signatures(
        node_id: str,
    ) -> list[dict[str, Any]]:
        """
        Creates function signatures for connected tools.

        Args:
            node_id: The node_id for which to create function signatures.

        Returns:
            List of function signatures for tools
        """
        db_client = get_database_manager_async_client()
        tools = [
            (link, node)
            for link, node in await db_client.get_connected_output_nodes(node_id)
            if is_tool_pin(link.source_name) and link.source_id == node_id
        ]
        if not tools:
            raise ValueError("There is no next node to execute.")

        return_tool_functions: list[dict[str, Any]] = []

        grouped_tool_links: dict[str, tuple["Node", list["Link"]]] = {}
        for link, node in tools:
            if link.sink_id not in grouped_tool_links:
                grouped_tool_links[link.sink_id] = (node, [link])
            else:
                grouped_tool_links[link.sink_id][1].append(link)

        for sink_node, links in grouped_tool_links.values():
            if not sink_node:
                raise ValueError(f"Sink node not found: {links[0].sink_id}")

            if sink_node.block_id == AgentExecutorBlock().id:
                tool_func = await OrchestratorBlock._create_agent_function_signature(
                    sink_node, links
                )
                return_tool_functions.append(tool_func)
            else:
                tool_func = await OrchestratorBlock._create_block_function_signature(
                    sink_node, links
                )
                return_tool_functions.append(tool_func)

        _disambiguate_tool_names(return_tool_functions)
        return return_tool_functions