def assistant_message_to_anthropic(message: AssistantMessage) -> MessageParam:
    assert_valid_name(message.source)

    if isinstance(message.content, list):
        # Tool calls
        tool_use_blocks: List[ToolUseBlock] = []

        for func_call in message.content:
            # Parse the arguments and convert to dict if it's a JSON string
            args = func_call.arguments
            args = __empty_content_to_whitespace(args)
            if isinstance(args, str):
                try:
                    json_objs = extract_json_from_str(args)
                    if len(json_objs) != 1:
                        raise ValueError(f"Expected a single JSON object, but found {len(json_objs)}")
                    args_dict = json_objs[0]
                except json.JSONDecodeError:
                    args_dict = {"text": args}
            else:
                args_dict = args

            tool_use_blocks.append(
                ToolUseBlock(
                    type="tool_use",
                    id=func_call.id,
                    name=func_call.name,
                    input=args_dict,
                )
            )

        # Include thought if available
        content_blocks: List[ContentBlock] = []
        if hasattr(message, "thought") and message.thought is not None:
            content_blocks.append(TextBlock(type="text", text=message.thought))

        content_blocks.extend(tool_use_blocks)

        return {
            "role": "assistant",
            "content": content_blocks,
        }
    else:
        # Simple text content
        return {
            "role": "assistant",
            "content": message.content,
        }