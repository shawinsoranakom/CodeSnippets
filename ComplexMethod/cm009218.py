def _make_message_chunk_from_anthropic_event(
        self,
        event: anthropic.types.RawMessageStreamEvent,
        *,
        stream_usage: bool = True,
        coerce_content_to_string: bool,
        block_start_event: anthropic.types.RawMessageStreamEvent | None = None,
    ) -> tuple[AIMessageChunk | None, anthropic.types.RawMessageStreamEvent | None]:
        """Convert Anthropic streaming event to `AIMessageChunk`.

        Args:
            event: Raw streaming event from Anthropic SDK
            stream_usage: Whether to include usage metadata in the output chunks.
            coerce_content_to_string: Whether to convert structured content to plain
                text strings.

                When `True`, only text content is preserved; when `False`, structured
                content like tool calls and citations are maintained.
            block_start_event: Previous content block start event, used for tracking
                tool use blocks and maintaining context across related events.

        Returns:
            Tuple with
                - `AIMessageChunk`: Converted message chunk with appropriate content and
                    metadata, or `None` if the event doesn't produce a chunk
                - `RawMessageStreamEvent`: Updated `block_start_event` for tracking
                    content blocks across sequential events, or `None` if not applicable

        Note:
            Not all Anthropic events result in message chunks. Events like internal
            state changes return `None` for the message chunk while potentially
            updating the `block_start_event` for context tracking.
        """
        message_chunk: AIMessageChunk | None = None
        # Reference: Anthropic SDK streaming implementation
        # https://github.com/anthropics/anthropic-sdk-python/blob/main/src/anthropic/lib/streaming/_messages.py  # noqa: E501
        if event.type == "message_start" and stream_usage:
            # Capture model name, but don't include usage_metadata yet
            # as it will be properly reported in message_delta with complete info
            if hasattr(event.message, "model"):
                response_metadata: dict[str, Any] = {"model_name": event.message.model}
            else:
                response_metadata = {}

            message_chunk = AIMessageChunk(
                content="" if coerce_content_to_string else [],
                response_metadata=response_metadata,
            )

        elif (
            event.type == "content_block_start"
            and event.content_block is not None
            and (
                "tool_result" in event.content_block.type
                or "tool_use" in event.content_block.type
                or "document" in event.content_block.type
                or "redacted_thinking" in event.content_block.type
            )
        ):
            if coerce_content_to_string:
                warnings.warn("Received unexpected tool content block.", stacklevel=2)

            content_block = event.content_block.model_dump()
            if "caller" in content_block and content_block["caller"] is None:
                content_block.pop("caller")
            content_block["index"] = event.index
            if event.content_block.type == "tool_use":
                if (
                    parsed_args := getattr(event.content_block, "input", None)
                ) and isinstance(parsed_args, dict):
                    # In some cases parsed args are represented in start event, with no
                    # following input_json_delta events
                    args = json.dumps(parsed_args)
                else:
                    args = ""
                tool_call_chunk = create_tool_call_chunk(
                    index=event.index,
                    id=event.content_block.id,
                    name=event.content_block.name,
                    args=args,
                )
                tool_call_chunks = [tool_call_chunk]
            else:
                tool_call_chunks = []
            message_chunk = AIMessageChunk(
                content=[content_block],
                tool_call_chunks=tool_call_chunks,
            )
            block_start_event = event

        # Process incremental content updates
        elif event.type == "content_block_delta":
            # Text and citation deltas (incremental text content)
            if event.delta.type in ("text_delta", "citations_delta"):
                if coerce_content_to_string and hasattr(event.delta, "text"):
                    text = getattr(event.delta, "text", "")
                    message_chunk = AIMessageChunk(content=text)
                else:
                    content_block = event.delta.model_dump()
                    content_block["index"] = event.index

                    # All citation deltas are part of a text block
                    content_block["type"] = "text"
                    if "citation" in content_block:
                        # Assign citations to a list if present
                        content_block["citations"] = [content_block.pop("citation")]
                    message_chunk = AIMessageChunk(content=[content_block])

            # Reasoning
            elif event.delta.type in {"thinking_delta", "signature_delta"}:
                content_block = event.delta.model_dump()
                content_block["index"] = event.index
                content_block["type"] = "thinking"
                message_chunk = AIMessageChunk(content=[content_block])

            # Tool input JSON (streaming tool arguments)
            elif event.delta.type == "input_json_delta":
                content_block = event.delta.model_dump()
                content_block["index"] = event.index
                start_event_block = (
                    getattr(block_start_event, "content_block", None)
                    if block_start_event
                    else None
                )
                if (
                    start_event_block is not None
                    and getattr(start_event_block, "type", None) == "tool_use"
                ):
                    tool_call_chunk = create_tool_call_chunk(
                        index=event.index,
                        id=None,
                        name=None,
                        args=event.delta.partial_json,
                    )
                    tool_call_chunks = [tool_call_chunk]
                else:
                    tool_call_chunks = []
                message_chunk = AIMessageChunk(
                    content=[content_block],
                    tool_call_chunks=tool_call_chunks,
                )

            # Compaction block
            elif event.delta.type == "compaction_delta":
                content_block = event.delta.model_dump()
                content_block["index"] = event.index
                content_block["type"] = "compaction"
                if (
                    "encrypted_content" in content_block
                    and content_block["encrypted_content"] is None
                ):
                    content_block.pop("encrypted_content")
                message_chunk = AIMessageChunk(content=[content_block])

        # Process final usage metadata and completion info
        elif event.type == "message_delta" and stream_usage:
            usage_metadata = _create_usage_metadata(event.usage)
            response_metadata = {
                "stop_reason": event.delta.stop_reason,
                "stop_sequence": event.delta.stop_sequence,
            }
            if context_management := getattr(event, "context_management", None):
                response_metadata["context_management"] = (
                    context_management.model_dump()
                )
            message_delta = getattr(event, "delta", None)
            if message_delta and (
                container := getattr(message_delta, "container", None)
            ):
                response_metadata["container"] = container.model_dump(mode="json")
            message_chunk = AIMessageChunk(
                content="" if coerce_content_to_string else [],
                usage_metadata=usage_metadata,
                response_metadata=response_metadata,
            )
            if message_chunk.response_metadata.get("stop_reason"):
                # Mark final Anthropic stream chunk
                message_chunk.chunk_position = "last"
        # Unhandled event types (e.g., `content_block_stop`, `ping` events)
        # https://platform.claude.com/docs/en/build-with-claude/streaming#other-events
        else:
            pass

        if message_chunk:
            message_chunk.response_metadata["model_provider"] = "anthropic"
        return message_chunk, block_start_event