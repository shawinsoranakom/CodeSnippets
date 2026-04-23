def convert_from_multiple_tool_calls_to_single_tool_call_messages(
    messages: list[dict],
    ignore_final_tool_result: bool = False,
) -> list[dict]:
    """Break one message with multiple tool calls into multiple messages."""
    converted_messages = []

    pending_tool_calls: dict[str, dict] = {}
    for message in messages:
        role, content = message['role'], message['content']
        if role == 'assistant':
            if message.get('tool_calls') and len(message['tool_calls']) > 1:
                # handle multiple tool calls by breaking them into multiple messages
                for i, tool_call in enumerate(message['tool_calls']):
                    pending_tool_calls[tool_call['id']] = {
                        'role': 'assistant',
                        'content': content if i == 0 else '',
                        'tool_calls': [tool_call],
                    }
            else:
                converted_messages.append(message)
        elif role == 'tool':
            if message['tool_call_id'] in pending_tool_calls:
                # remove the tool call from the pending list
                _tool_call_message = pending_tool_calls.pop(message['tool_call_id'])
                converted_messages.append(_tool_call_message)
                # add the tool result
                converted_messages.append(message)
            else:
                assert len(pending_tool_calls) == 0, (
                    f'Found pending tool calls but not found in pending list: {pending_tool_calls=}'
                )
                converted_messages.append(message)
        else:
            assert len(pending_tool_calls) == 0, (
                f'Found pending tool calls but not expect to handle it with role {role}: {pending_tool_calls=}, {message=}'
            )
            converted_messages.append(message)

    if not ignore_final_tool_result and len(pending_tool_calls) > 0:
        raise FunctionCallConversionError(
            f'Found pending tool calls but no tool result: {pending_tool_calls=}'
        )
    return converted_messages