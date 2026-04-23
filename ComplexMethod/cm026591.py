async def _transform_stream(  # noqa: C901 - This is complex, but better to have it in one place
    chat_log: conversation.ChatLog,
    stream: AsyncStream[MessageStreamEvent],
    output_tool: str | None = None,
) -> AsyncGenerator[
    conversation.AssistantContentDeltaDict | conversation.ToolResultContentDeltaDict
]:
    """Transform the response stream into HA format.

    A typical stream of responses might look something like the following:
    - RawMessageStartEvent with no content
    - RawContentBlockStartEvent with an empty ThinkingBlock (if extended thinking is enabled)
    - RawContentBlockDeltaEvent with a ThinkingDelta
    - RawContentBlockDeltaEvent with a ThinkingDelta
    - RawContentBlockDeltaEvent with a ThinkingDelta
    - ...
    - RawContentBlockDeltaEvent with a SignatureDelta
    - RawContentBlockStopEvent
    - RawContentBlockStartEvent with a RedactedThinkingBlock (occasionally)
    - RawContentBlockStopEvent (RedactedThinkingBlock does not have a delta)
    - RawContentBlockStartEvent with an empty TextBlock
    - RawContentBlockDeltaEvent with a TextDelta
    - RawContentBlockDeltaEvent with a TextDelta
    - RawContentBlockDeltaEvent with a TextDelta
    - ...
    - RawContentBlockStopEvent
    - RawContentBlockStartEvent with ToolUseBlock specifying the function name
    - RawContentBlockDeltaEvent with a InputJSONDelta
    - RawContentBlockDeltaEvent with a InputJSONDelta
    - ...
    - RawContentBlockStopEvent
    - RawMessageDeltaEvent with a stop_reason='tool_use'
    - RawMessageStopEvent(type='message_stop')

    Each message could contain multiple blocks of the same type.
    """
    if stream is None or not hasattr(stream, "__aiter__"):
        raise HomeAssistantError(
            translation_domain=DOMAIN, translation_key="unexpected_stream_object"
        )

    current_tool_block: ToolUseBlockParam | ServerToolUseBlockParam | None = None
    current_tool_args: str
    content_details = ContentDetails()
    content_details.add_citation_detail()
    input_usage: Usage | None = None
    first_block: bool = True

    async for response in stream:
        LOGGER.debug("Received response: %s", response)

        if isinstance(response, RawMessageStartEvent):
            input_usage = response.message.usage
            first_block = True
        elif isinstance(response, RawContentBlockStartEvent):
            if isinstance(response.content_block, ToolUseBlock):
                current_tool_block = ToolUseBlockParam(
                    type="tool_use",
                    id=response.content_block.id,
                    name=response.content_block.name,
                    input=response.content_block.input or {},
                )
                current_tool_args = ""
                if response.content_block.name == output_tool:
                    if first_block or content_details.has_content():
                        if content_details:
                            content_details.delete_empty()
                            yield {"native": content_details}
                        content_details = ContentDetails()
                        content_details.add_citation_detail()
                        yield {"role": "assistant"}
                        first_block = False
            elif isinstance(response.content_block, TextBlock):
                if (  # Do not start a new assistant content just for citations, concatenate consecutive blocks with citations instead.
                    first_block
                    or (
                        not content_details.has_citations()
                        and response.content_block.citations is None
                        and content_details.has_content()
                    )
                ):
                    if content_details:
                        content_details.delete_empty()
                        yield {"native": content_details}
                    content_details = ContentDetails()
                    yield {"role": "assistant"}
                    first_block = False
                content_details.add_citation_detail()
                if response.content_block.text:
                    content_details.citation_details[-1].length += len(
                        response.content_block.text
                    )
                    yield {"content": response.content_block.text}
            elif isinstance(response.content_block, ThinkingBlock):
                if first_block or content_details.thinking_signature:
                    if content_details:
                        content_details.delete_empty()
                        yield {"native": content_details}
                    content_details = ContentDetails()
                    content_details.add_citation_detail()
                    yield {"role": "assistant"}
                    first_block = False
            elif isinstance(response.content_block, RedactedThinkingBlock):
                LOGGER.debug(
                    "Some of Claude’s internal reasoning has been automatically "
                    "encrypted for safety reasons. This doesn’t affect the quality of "
                    "responses"
                )
                if first_block or content_details.redacted_thinking:
                    if content_details:
                        content_details.delete_empty()
                        yield {"native": content_details}
                    content_details = ContentDetails()
                    content_details.add_citation_detail()
                    yield {"role": "assistant"}
                    first_block = False
                content_details.redacted_thinking = response.content_block.data
            elif isinstance(response.content_block, ServerToolUseBlock):
                current_tool_block = ServerToolUseBlockParam(
                    type="server_tool_use",
                    id=response.content_block.id,
                    name=response.content_block.name,
                    input=response.content_block.input or {},
                )
                current_tool_args = ""
            elif isinstance(
                response.content_block,
                (
                    WebSearchToolResultBlock,
                    CodeExecutionToolResultBlock,
                    BashCodeExecutionToolResultBlock,
                    TextEditorCodeExecutionToolResultBlock,
                    ToolSearchToolResultBlock,
                ),
            ):
                if content_details:
                    content_details.delete_empty()
                    yield {"native": content_details}
                content_details = ContentDetails()
                content_details.add_citation_detail()
                yield {
                    "role": "tool_result",
                    "tool_call_id": response.content_block.tool_use_id,
                    "tool_name": response.content_block.type.removesuffix(
                        "_tool_result"
                    ),
                    "tool_result": {
                        "content": cast(
                            JsonObjectType, response.content_block.to_dict()["content"]
                        )
                    }
                    if isinstance(response.content_block.content, list)
                    else cast(JsonObjectType, response.content_block.content.to_dict()),
                }
                first_block = True
        elif isinstance(response, RawContentBlockDeltaEvent):
            if isinstance(response.delta, InputJSONDelta):
                if (
                    current_tool_block is not None
                    and current_tool_block["name"] == output_tool
                ):
                    content_details.citation_details[-1].length += len(
                        response.delta.partial_json
                    )
                    yield {"content": response.delta.partial_json}
                else:
                    current_tool_args += response.delta.partial_json
            elif isinstance(response.delta, TextDelta):
                if response.delta.text:
                    content_details.citation_details[-1].length += len(
                        response.delta.text
                    )
                    yield {"content": response.delta.text}
            elif isinstance(response.delta, ThinkingDelta):
                if response.delta.thinking:
                    yield {"thinking_content": response.delta.thinking}
            elif isinstance(response.delta, SignatureDelta):
                content_details.thinking_signature = response.delta.signature
            elif isinstance(response.delta, CitationsDelta):
                content_details.add_citation(response.delta.citation)
        elif isinstance(response, RawContentBlockStopEvent):
            if current_tool_block is not None:
                if current_tool_block["name"] == output_tool:
                    current_tool_block = None
                    continue
                tool_args = json.loads(current_tool_args) if current_tool_args else {}
                current_tool_block["input"] |= tool_args
                yield {
                    "tool_calls": [
                        llm.ToolInput(
                            id=current_tool_block["id"],
                            tool_name=current_tool_block["name"],
                            tool_args=current_tool_block["input"],
                            external=current_tool_block["type"] == "server_tool_use",
                        )
                    ]
                }
                current_tool_block = None
        elif isinstance(response, RawMessageDeltaEvent):
            if (usage := response.usage) is not None:
                chat_log.async_trace(_create_token_stats(input_usage, usage))
            content_details.container = response.delta.container
            if response.delta.stop_reason == "refusal":
                raise HomeAssistantError(
                    translation_domain=DOMAIN, translation_key="api_refusal"
                )
        elif isinstance(response, RawMessageStopEvent):
            if content_details:
                content_details.delete_empty()
                yield {"native": content_details}
            content_details = ContentDetails()
            content_details.add_citation_detail()