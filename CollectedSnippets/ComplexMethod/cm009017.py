def tools_to_model(state: dict[str, Any]) -> str | None:
        last_ai_message, tool_messages = _fetch_last_ai_and_tool_messages(state["messages"])

        # 1. If no AIMessage exists (e.g., messages were cleared), route to model
        if last_ai_message is None:
            return model_destination

        # 2. Exit condition: All executed tools have return_direct=True
        # Filter to only client-side tools (provider tools are not in tool_node)
        client_side_tool_calls = [
            c for c in last_ai_message.tool_calls if c["name"] in tool_node.tools_by_name
        ]
        if client_side_tool_calls and all(
            tool_node.tools_by_name[c["name"]].return_direct for c in client_side_tool_calls
        ):
            return end_destination

        # 3. Exit condition: A structured output tool was executed
        if any(t.name in structured_output_tools for t in tool_messages):
            return end_destination

        # 4. Default: Continue the loop
        #    Tool execution completed successfully, route back to the model
        #    so it can process the tool results and decide the next action.
        return model_destination