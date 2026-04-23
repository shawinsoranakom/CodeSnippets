def sharegpt_converter(raw_sample: SharegptSample) -> SFTSample:
    """Convert ShareGPT sample to SFT sample.

    See raw example at: https://huggingface.co/datasets/llamafactory/glaive_toolcall_en

    Args:
        raw_sample (SharegptSample): ShareGPT sample.

    Returns:
        SFTSample: SFT sample.
    """
    tag_mapping = {
        "system": "system",
        "human": "user",
        "gpt": "assistant",
        "observation": "tool",
        "function_call": "assistant",
    }
    sample = {}
    messages = []
    for message in raw_sample.get("conversations", []):
        tag = message["from"]
        if tag not in tag_mapping:
            logger.warning_rank0(f"Unsupported role tag {tag} in message: {message}")
        elif tag == "function_call":
            try:
                tool_calls: ToolCall | list[ToolCall] = json.loads(message["value"])
            except json.JSONDecodeError:
                logger.warning_rank0(f"Invalid tool call format: {str(message['value'])}")
                continue

            if not isinstance(tool_calls, list):
                tool_calls = [tool_calls]

            messages.append(
                {
                    "role": "assistant",
                    "content": [{"type": "tool_call", "value": json.dumps(tool_call)} for tool_call in tool_calls],
                    "loss_weight": 1.0,
                }
            )
        else:
            messages.append(
                {
                    "role": tag_mapping[tag],
                    "content": [{"type": "text", "value": message["value"]}],
                    "loss_weight": 1.0 if tag == "gpt" else 0.0,
                }
            )

    sample["messages"] = messages

    tools = raw_sample.get("tools")
    if tools:
        try:
            tools: list[dict[str, Any]] = json.loads(tools)
            sample["tools"] = json.dumps(tools)
        except json.JSONDecodeError:
            logger.warning_rank0(f"Invalid tools format: {str(tools)}")

    return sample