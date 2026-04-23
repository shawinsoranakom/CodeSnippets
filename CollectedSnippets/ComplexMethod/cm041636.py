def process_message(raw_messages: list[OpenaiMessage]):
        messages = []
        for message in raw_messages:
            if message["role"] == "tool":
                try:
                    tool_calls: ToolCall | list[ToolCall] = json.loads(message["content"])
                except json.JSONDecodeError:
                    logger.warning_rank0(f"Invalid tool call format: {str(message['content'])}")
                    continue

                if not isinstance(tool_calls, list):
                    tool_calls = [tool_calls]

                messages.append(
                    {
                        "role": message["role"],
                        "content": [{"type": "tool_call", "value": json.dumps(tool_call)} for tool_call in tool_calls],
                        "loss_weight": 1.0 if message["role"] == "assistant" else 0.0,
                    }
                )
            else:
                messages.append(
                    {
                        "role": message["role"],
                        "content": [{"type": "text", "value": message["content"]}],
                        "loss_weight": 1.0 if message["role"] == "assistant" else 0.0,
                    }
                )

        return messages