def _normalize_messages(
    messages: Sequence["BaseMessage"],
) -> list["BaseMessage"]:
    """Normalize message formats to LangChain v1 standard content blocks.

    Chat models already implement support for:
    - Images in OpenAI Chat Completions format
        These will be passed through unchanged
    - LangChain v1 standard content blocks

    This function extends support to:
    - `[Audio](https://platform.openai.com/docs/api-reference/chat/create) and
        `[file](https://platform.openai.com/docs/api-reference/files) data in OpenAI
        Chat Completions format
        - Images are technically supported but we expect chat models to handle them
            directly; this may change in the future
    - LangChain v0 standard content blocks for backward compatibility

    !!! warning "Behavior changed in `langchain-core` 1.0.0"

        In previous versions, this function returned messages in LangChain v0 format.
        Now, it returns messages in LangChain v1 format, which upgraded chat models now
        expect to receive when passing back in message history. For backward
        compatibility, this function will convert v0 message content to v1 format.

    ??? note "v0 Content Block Schemas"

        `URLContentBlock`:

        ```python
        {
            mime_type: NotRequired[str]
            type: Literal['image', 'audio', 'file'],
            source_type: Literal['url'],
            url: str,
        }
        ```

        `Base64ContentBlock`:

        ```python
        {
            mime_type: NotRequired[str]
            type: Literal['image', 'audio', 'file'],
            source_type: Literal['base64'],
            data: str,
        }
        ```

        `IDContentBlock`:

        (In practice, this was never used)

        ```python
        {
            type: Literal["image", "audio", "file"],
            source_type: Literal["id"],
            id: str,
        }
        ```

        `PlainTextContentBlock`:

        ```python
        {
            mime_type: NotRequired[str]
            type: Literal['file'],
            source_type: Literal['text'],
            url: str,
        }
        ```

    If a v1 message is passed in, it will be returned as-is, meaning it is safe to
    always pass in v1 messages to this function for assurance.

    For posterity, here are the OpenAI Chat Completions schemas we expect:

    Chat Completions image. Can be URL-based or base64-encoded. Supports MIME types
    png, jpeg/jpg, webp, static gif:
    {
        "type": Literal['image_url'],
        "image_url": {
            "url": Union["data:$MIME_TYPE;base64,$BASE64_ENCODED_IMAGE", "$IMAGE_URL"],
            "detail": Literal['low', 'high', 'auto'] = 'auto',  # Supported by OpenAI
        }
    }

    Chat Completions audio:
    {
        "type": Literal['input_audio'],
        "input_audio": {
            "format": Literal['wav', 'mp3'],
            "data": str = "$BASE64_ENCODED_AUDIO",
        },
    }

    Chat Completions files: either base64 or pre-uploaded file ID
    {
        "type": Literal['file'],
        "file": Union[
            {
                "filename": str | None = "$FILENAME",
                "file_data": str = "$BASE64_ENCODED_FILE",
            },
            {
                "file_id": str = "$FILE_ID",  # For pre-uploaded files to OpenAI
            },
        ],
    }

    """
    from langchain_core.messages.block_translators.langchain_v0 import (  # noqa: PLC0415
        _convert_legacy_v0_content_block_to_v1,
    )
    from langchain_core.messages.block_translators.openai import (  # noqa: PLC0415
        _convert_openai_format_to_data_block,
    )

    formatted_messages = []
    for message in messages:
        # We preserve input messages - the caller may reuse them elsewhere and expects
        # them to remain unchanged. We only create a copy if we need to translate.
        formatted_message = message

        if isinstance(message.content, list):
            for idx, block in enumerate(message.content):
                # OpenAI Chat Completions multimodal data blocks to v1 standard
                if (
                    isinstance(block, dict)
                    and block.get("type") in {"input_audio", "file"}
                    # Discriminate between OpenAI/LC format since they share `'type'`
                    and is_openai_data_block(block)
                ):
                    formatted_message = _ensure_message_copy(message, formatted_message)

                    converted_block = _convert_openai_format_to_data_block(block)
                    _update_content_block(formatted_message, idx, converted_block)

                # Convert multimodal LangChain v0 to v1 standard content blocks
                elif (
                    isinstance(block, dict)
                    and block.get("type")
                    in {
                        "image",
                        "audio",
                        "file",
                    }
                    and block.get("source_type")  # v1 doesn't have `source_type`
                    in {
                        "url",
                        "base64",
                        "id",
                        "text",
                    }
                ):
                    formatted_message = _ensure_message_copy(message, formatted_message)

                    converted_block = _convert_legacy_v0_content_block_to_v1(block)
                    _update_content_block(formatted_message, idx, converted_block)
                    continue

                # else, pass through blocks that look like they have v1 format unchanged

        formatted_messages.append(formatted_message)

    return formatted_messages