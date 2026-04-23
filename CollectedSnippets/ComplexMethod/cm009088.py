def _oai_structured_outputs_parser(
    ai_msg: AIMessage, schema: type[_BM]
) -> PydanticBaseModel | None:
    if (parsed := ai_msg.additional_kwargs.get("parsed")) is not None:
        if isinstance(parsed, dict):
            return schema(**parsed)
        return parsed
    if ai_msg.additional_kwargs.get("refusal"):
        raise OpenAIRefusalError(ai_msg.additional_kwargs["refusal"])
    if any(
        isinstance(block, dict)
        and block.get("type") == "non_standard"
        and "refusal" in block["value"]  # type: ignore[typeddict-item]
        for block in ai_msg.content_blocks
    ):
        refusal = next(
            block["value"]["refusal"]
            for block in ai_msg.content_blocks
            if isinstance(block, dict)
            and block["type"] == "non_standard"
            and "refusal" in block["value"]
        )
        raise OpenAIRefusalError(refusal)
    if ai_msg.tool_calls:
        return None
    msg = (
        "Structured Output response does not have a 'parsed' field nor a 'refusal' "
        f"field. Received message:\n\n{ai_msg}"
    )
    raise ValueError(msg)