async def mock_generator(events: Iterable[RawMessageStreamEvent], **kwargs):
        """Create a stream of messages with the specified content blocks."""
        stop_reason = "end_turn"
        container = None
        refusal_magic_string = "ANTHROPIC_MAGIC_STRING_TRIGGER_REFUSAL_1FAEFB6177B4672DEE07F9D3AFC62588CCD2631EDCF22E8CCC1FB35B501C9C86"
        for message in kwargs.get("messages"):
            if message["role"] != "user":
                continue
            if isinstance(message["content"], str):
                if refusal_magic_string in message["content"]:
                    stop_reason = "refusal"
                    break
            else:
                for content in message["content"]:
                    if content.get(
                        "type"
                    ) == "text" and refusal_magic_string in content.get("text", ""):
                        stop_reason = "refusal"
                        break

        yield RawMessageStartEvent(
            message=Message(
                type="message",
                id="msg_1234567890ABCDEFGHIJKLMN",
                content=[],
                role="assistant",
                model=kwargs["model"],
                usage=Usage(input_tokens=0, output_tokens=0),
            ),
            type="message_start",
        )
        for event in events:
            if isinstance(event, RawContentBlockStartEvent) and isinstance(
                event.content_block, ToolUseBlock
            ):
                stop_reason = "tool_use"
            elif (
                isinstance(event, RawContentBlockStartEvent)
                and isinstance(event.content_block, ServerToolUseBlock)
                and event.content_block.name
                in [
                    "code_execution",
                    "bash_code_execution",
                    "text_editor_code_execution",
                ]
            ):
                container = Container(
                    id=kwargs.get("container_id", "container_1234567890ABCDEFGHIJKLMN"),
                    expires_at=datetime.datetime.now(tz=datetime.UTC)
                    + datetime.timedelta(minutes=5),
                )

            yield event
        yield RawMessageDeltaEvent(
            type="message_delta",
            delta=Delta(
                stop_reason=stop_reason,
                stop_sequence="",
                container=container,
            ),
            usage=MessageDeltaUsage(output_tokens=0),
        )
        yield RawMessageStopEvent(type="message_stop")