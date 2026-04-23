def _format_for_tracing(messages: list[BaseMessage]) -> list[BaseMessage]:
    """Format messages for tracing in `on_chat_model_start`.

    - Update image content blocks to OpenAI Chat Completions format (backward
    compatibility).
    - Add `type` key to content blocks that have a single key.

    Args:
        messages: List of messages to format.

    Returns:
        List of messages formatted for tracing.

    """
    messages_to_trace = []
    for message in messages:
        message_to_trace = message
        if isinstance(message.content, list):
            for idx, block in enumerate(message.content):
                if isinstance(block, dict):
                    # Update image content blocks to OpenAI # Chat Completions format.
                    if (
                        block.get("type") == "image"
                        and is_data_content_block(block)
                        and not ("file_id" in block or block.get("source_type") == "id")
                    ):
                        if message_to_trace is message:
                            # Shallow copy
                            message_to_trace = message.model_copy()
                            message_to_trace.content = list(message_to_trace.content)

                        message_to_trace.content[idx] = (  # type: ignore[index]  # mypy confused by .model_copy
                            convert_to_openai_image_block(block)
                        )
                    elif (
                        block.get("type") == "file"
                        and is_data_content_block(block)  # v0 (image/audio/file) or v1
                        and "base64" in block
                        # Backward compat: convert v1 base64 blocks to v0
                    ):
                        if message_to_trace is message:
                            # Shallow copy
                            message_to_trace = message.model_copy()
                            message_to_trace.content = list(message_to_trace.content)

                        message_to_trace.content[idx] = {  # type: ignore[index]
                            **{k: v for k, v in block.items() if k != "base64"},
                            "data": block["base64"],
                            "source_type": "base64",
                        }
                    elif len(block) == 1 and "type" not in block:
                        # Tracing assumes all content blocks have a "type" key. Here
                        # we add this key if it is missing, and there's an obvious
                        # choice for the type (e.g., a single key in the block).
                        if message_to_trace is message:
                            # Shallow copy
                            message_to_trace = message.model_copy()
                            message_to_trace.content = list(message_to_trace.content)
                        key = next(iter(block))
                        message_to_trace.content[idx] = {  # type: ignore[index]
                            "type": key,
                            key: block[key],
                        }
        messages_to_trace.append(message_to_trace)

    return messages_to_trace