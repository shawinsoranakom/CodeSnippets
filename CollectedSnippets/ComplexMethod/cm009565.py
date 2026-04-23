def count_tokens_approximately(
    messages: Iterable[MessageLikeRepresentation],
    *,
    chars_per_token: float = 4.0,
    extra_tokens_per_message: float = 3.0,
    count_name: bool = True,
    tokens_per_image: int = 85,
    use_usage_metadata_scaling: bool = False,
    tools: list[BaseTool | dict[str, Any]] | None = None,
) -> int:
    """Approximate the total number of tokens in messages.

    The token count includes stringified message content, role, and (optionally) name.

    - For AI messages, the token count also includes stringified tool calls.
    - For tool messages, the token count also includes the tool call ID.
    - For multimodal messages with images, applies a fixed token penalty per image
      instead of counting base64-encoded characters.
    - If tools are provided, the token count also includes stringified tool schemas.

    Args:
        messages: List of messages to count tokens for.
        chars_per_token: Number of characters per token to use for the approximation.
            One token corresponds to ~4 chars for common English text.
            You can also specify `float` values for more fine-grained control.
            [See more here](https://platform.openai.com/tokenizer).
        extra_tokens_per_message: Number of extra tokens to add per message, e.g.
            special tokens, including beginning/end of message.
            You can also specify `float` values for more fine-grained control.
            [See more here](https://github.com/openai/openai-cookbook/blob/main/examples/How_to_count_tokens_with_tiktoken.ipynb).
        count_name: Whether to include message names in the count.
        tokens_per_image: Fixed token cost per image (default: 85, aligned with
            OpenAI's low-resolution image token cost).
        use_usage_metadata_scaling: If True, and all AI messages have consistent
            `response_metadata['model_provider']`, scale the approximate token count
            using the **most recent** AI message that has
            `usage_metadata['total_tokens']`. The scaling factor is:
            `AI_total_tokens / approx_tokens_up_to_that_AI_message`
        tools: List of tools to include in the token count. Each tool can be either
            a `BaseTool` instance or a dict representing a tool schema. `BaseTool`
            instances are converted to OpenAI tool format before counting.

    Returns:
        Approximate number of tokens in the messages (and tools, if provided).

    Note:
        This is a simple approximation that may not match the exact token count used by
        specific models. For accurate counts, use model-specific tokenizers.

        For multimodal messages containing images, a fixed token penalty is applied
        per image instead of counting base64-encoded characters, which provides a
        more realistic approximation.

    !!! version-added "Added in `langchain-core` 0.3.46"
    """
    converted_messages = convert_to_messages(messages)

    token_count = 0.0

    ai_model_provider: str | None = None
    invalid_model_provider = False
    last_ai_total_tokens: int | None = None
    approx_at_last_ai: float | None = None

    # Count tokens for tools if provided
    if tools:
        tools_chars = 0
        for tool in tools:
            tool_dict = tool if isinstance(tool, dict) else convert_to_openai_tool(tool)
            tools_chars += len(json.dumps(tool_dict))
        token_count += math.ceil(tools_chars / chars_per_token)

    for message in converted_messages:
        message_chars = 0

        if isinstance(message.content, str):
            message_chars += len(message.content)
        # Handle multimodal content (list of content blocks)
        elif isinstance(message.content, list):
            for block in message.content:
                if isinstance(block, str):
                    # String block
                    message_chars += len(block)
                elif isinstance(block, dict):
                    block_type = block.get("type", "")

                    # Apply fixed penalty for image blocks
                    if block_type in {"image", "image_url"}:
                        token_count += tokens_per_image
                    # Count text blocks normally
                    elif block_type == "text":
                        text = block.get("text", "")
                        message_chars += len(text)
                    # Conservative estimate for unknown block types
                    else:
                        message_chars += len(repr(block))
                else:
                    # Fallback for unexpected block types
                    message_chars += len(repr(block))
        else:
            # Fallback for other content types
            content = repr(message.content)
            message_chars += len(content)

        if (
            isinstance(message, AIMessage)
            # exclude Anthropic format as tool calls are already included in the content
            and not isinstance(message.content, list)
            and message.tool_calls
        ):
            tool_calls_content = repr(message.tool_calls)
            message_chars += len(tool_calls_content)

        if isinstance(message, ToolMessage):
            message_chars += len(message.tool_call_id)

        role = _get_message_openai_role(message)
        message_chars += len(role)

        if message.name and count_name:
            message_chars += len(message.name)

        # NOTE: we're rounding up per message to ensure that
        # individual message token counts add up to the total count
        # for a list of messages
        token_count += math.ceil(message_chars / chars_per_token)

        # add extra tokens per message
        token_count += extra_tokens_per_message

        if use_usage_metadata_scaling and isinstance(message, AIMessage):
            model_provider = message.response_metadata.get("model_provider")
            if ai_model_provider is None:
                ai_model_provider = model_provider
            elif model_provider != ai_model_provider:
                invalid_model_provider = True

            if message.usage_metadata and isinstance(
                (total_tokens := message.usage_metadata.get("total_tokens")), int
            ):
                last_ai_total_tokens = total_tokens
                approx_at_last_ai = token_count

    if (
        use_usage_metadata_scaling
        and len(converted_messages) > 1
        and not invalid_model_provider
        and ai_model_provider is not None
        and last_ai_total_tokens is not None
        and approx_at_last_ai
        and approx_at_last_ai > 0
    ):
        scale_factor = last_ai_total_tokens / approx_at_last_ai
        token_count *= min(1.25, max(1.0, scale_factor))

    # round up once more time in case extra_tokens_per_message is a float
    return math.ceil(token_count)