def _prepare_apply_chat_template_tools_and_messages(
    messages: list["ChatCompletionMessageParam"],
    tools: list[dict[str, Any]] | None = None,
    continue_final_message: bool = False,
    add_generation_prompt: bool = False,
) -> tuple[list["ChatCompletionMessageParam"], list[dict[str, Any]] | None]:
    if add_generation_prompt and continue_final_message:
        raise ValueError(
            "Cannot set both `add_generation_prompt` and "
            "`continue_final_message` to True."
        )

    last_message = cast(dict[str, Any], messages[-1])
    # add_generation_prompt is directly handled by the tokenizer but we
    # check if the user is trying to use it with a final assistant message
    # which is probably not what they want.
    # If add_generation_prompt is False, we don't need to check anything.
    if add_generation_prompt and last_message["role"] == "assistant":
        raise ValueError(
            "Cannot set `add_generation_prompt` to True when "
            "the last message is from the assistant. Consider "
            "using `continue_final_message` instead."
        )
    if continue_final_message and last_message["role"] != "assistant":
        raise ValueError(
            "Cannot set `continue_final_message` to True when "
            "the last message is not from the assistant."
        )

    # mistral-common requires AssistantMessage content to be string [1].
    #
    # [1]: https://github.com/mistralai/mistral-common/blob/f4a06998b75ed78bbf5aaf569590b772ea26c9f6/src/mistral_common/protocol/instruct/messages.py#L80
    for message in messages:
        # Remove reasoning as unsupported by Mistral
        _ = message.pop("reasoning", None)  # type: ignore

    tools = (
        [adapt_inplace_to_mistral_tool(tool=tool) for tool in tools]
        if tools is not None
        else None
    )

    return messages, tools