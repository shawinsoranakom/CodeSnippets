def _filter_unmatched_tool_calls(
        messages: list[Message],
    ) -> Generator[Message, None, None]:
        """Filter out tool calls that don't have matching tool responses and vice versa.

        This ensures that every tool_call_id in a tool message has a corresponding tool_calls[].id
        in an assistant message, and vice versa. The original list is unmodified, when tool_calls is
        updated the message is copied.

        This does not remove items with id set to None.
        """
        tool_call_ids = {
            tool_call.id
            for message in messages
            if message.tool_calls
            for tool_call in message.tool_calls
            if message.role == 'assistant' and tool_call.id
        }
        tool_response_ids = {
            message.tool_call_id
            for message in messages
            if message.role == 'tool' and message.tool_call_id
        }

        for message in messages:
            # Remove tool messages with no matching assistant tool call
            if message.role == 'tool' and message.tool_call_id:
                if message.tool_call_id in tool_call_ids:
                    yield message

            # Remove assistant tool calls with no matching tool response
            elif message.role == 'assistant' and message.tool_calls:
                all_tool_calls_match = all(
                    tool_call.id in tool_response_ids
                    for tool_call in message.tool_calls
                )
                if all_tool_calls_match:
                    yield message
                else:
                    matched_tool_calls = [
                        tool_call
                        for tool_call in message.tool_calls
                        if tool_call.id in tool_response_ids
                    ]

                    if matched_tool_calls:
                        # Keep an updated message if there are tools calls left
                        yield message.model_copy(
                            update={'tool_calls': matched_tool_calls}
                        )
            else:
                # Any other case is kept
                yield message