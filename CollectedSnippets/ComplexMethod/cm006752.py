async def handle_on_tool_end(
    event: dict[str, Any],
    agent_message: Message,
    tool_blocks_map: dict[str, ToolContent],
    send_message_callback: SendMessageFunctionType,
    start_time: float,
) -> tuple[Message, float]:
    run_id = event.get("run_id", "")
    tool_name = event.get("name", "")
    tool_key = f"{tool_name}_{run_id}"
    tool_content = tool_blocks_map.get(tool_key)

    if tool_content and isinstance(tool_content, ToolContent):
        # Call send_message_callback first to get the updated message structure
        agent_message = await send_message_callback(message=agent_message, skip_db_update=True)
        new_start_time = perf_counter()

        # Now find and update the tool content in the current message
        duration = _calculate_duration(start_time)
        tool_key = f"{tool_name}_{run_id}"

        # Find the corresponding tool content in the updated message
        updated_tool_content = None
        if agent_message.content_blocks and agent_message.content_blocks[0].contents:
            for content in agent_message.content_blocks[0].contents:
                if (
                    isinstance(content, ToolContent)
                    and content.name == tool_name
                    and content.tool_input == tool_content.tool_input
                ):
                    updated_tool_content = content
                    break

        # Update the tool content that's actually in the message
        if updated_tool_content:
            updated_tool_content.duration = duration
            updated_tool_content.header = {"title": f"Executed **{updated_tool_content.name}**", "icon": "Hammer"}
            updated_tool_content.output = event["data"].get("output")

            # Update the map reference
            tool_blocks_map[tool_key] = updated_tool_content

        return agent_message, new_start_time
    return agent_message, start_time