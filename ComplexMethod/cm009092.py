def _make_computer_call_output_from_message(
    message: ToolMessage,
) -> dict[str, Any] | None:
    computer_call_output: dict[str, Any] | None = None
    if isinstance(message.content, list):
        for block in message.content:
            if (
                message.additional_kwargs.get("type") == "computer_call_output"
                and isinstance(block, dict)
                and block.get("type") == "input_image"
            ):
                # Use first input_image block
                computer_call_output = {
                    "call_id": message.tool_call_id,
                    "type": "computer_call_output",
                    "output": block,
                }
                break
            if (
                isinstance(block, dict)
                and block.get("type") == "non_standard"
                and block.get("value", {}).get("type") == "computer_call_output"
            ):
                computer_call_output = block["value"]
                break
    elif message.additional_kwargs.get("type") == "computer_call_output":
        # string, assume image_url
        computer_call_output = {
            "call_id": message.tool_call_id,
            "type": "computer_call_output",
            "output": {"type": "input_image", "image_url": message.content},
        }
    if (
        computer_call_output is not None
        and "acknowledged_safety_checks" in message.additional_kwargs
    ):
        computer_call_output["acknowledged_safety_checks"] = message.additional_kwargs[
            "acknowledged_safety_checks"
        ]
    return computer_call_output