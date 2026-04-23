def _convert_from_v1_to_mistral(
    content: list[types.ContentBlock],
    model_provider: str | None,
) -> str | list[str | dict]:
    new_content: list = []
    for block in content:
        if block["type"] == "text":
            new_content.append({"text": block.get("text", ""), "type": "text"})

        elif (
            block["type"] == "reasoning"
            and (reasoning := block.get("reasoning"))
            and isinstance(reasoning, str)
            and model_provider == "mistralai"
        ):
            new_content.append(
                {
                    "type": "thinking",
                    "thinking": [{"type": "text", "text": reasoning}],
                }
            )

        elif (
            block["type"] == "non_standard"
            and "value" in block
            and model_provider == "mistralai"
        ):
            new_content.append(block["value"])
        elif block["type"] == "tool_call":
            continue
        else:
            new_content.append(block)

    return new_content