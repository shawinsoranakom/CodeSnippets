def model_to_tools(
        state: dict[str, Any],
    ) -> str | list[Send] | None:
        # 1. If there's an explicit jump_to in the state, use it
        if jump_to := state.get("jump_to"):
            return _resolve_jump(
                jump_to,
                model_destination=model_destination,
                end_destination=end_destination,
            )

        last_ai_message, tool_messages = _fetch_last_ai_and_tool_messages(state["messages"])

        # 2. if no AIMessage exists (e.g., messages were cleared), exit the loop
        if last_ai_message is None:
            return end_destination

        tool_message_ids = [m.tool_call_id for m in tool_messages]

        # 3. If the model hasn't called any tools, exit the loop
        # this is the classic exit condition for an agent loop
        if len(last_ai_message.tool_calls) == 0:
            return end_destination

        pending_tool_calls = [
            c
            for c in last_ai_message.tool_calls
            if c["id"] not in tool_message_ids and c["name"] not in structured_output_tools
        ]

        # 4. If there are pending tool calls, jump to the tool node
        if pending_tool_calls:
            return [
                Send(
                    "tools",
                    ToolCallWithContext(
                        __type="tool_call_with_context",
                        tool_call=tool_call,
                        state=state,
                    ),
                )
                for tool_call in pending_tool_calls
            ]

        # 5. If there is a structured response, exit the loop
        if "structured_response" in state:
            return end_destination

        # 6. AIMessage has tool calls, but there are no pending tool calls which suggests
        # the injection of artificial tool messages. Jump to the model node
        return model_destination