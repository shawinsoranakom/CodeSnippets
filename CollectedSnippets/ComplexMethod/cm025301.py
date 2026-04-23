async def _transform_stream(  # noqa: C901 - This is complex, but better to have it in one place
    chat_log: conversation.ChatLog,
    stream: AsyncStream[ResponseStreamEvent],
    remove_citations: bool = False,
) -> AsyncGenerator[
    conversation.AssistantContentDeltaDict | conversation.ToolResultContentDeltaDict
]:
    """Transform an OpenAI delta stream into HA format."""
    last_summary_index = None
    last_role: Literal["assistant", "tool_result"] | None = None

    # Non-reasoning models don't follow our request to remove citations, so we remove
    # them manually here. They always follow the same pattern: the citation is always
    # in parentheses in Markdown format, the citation is always in a single delta event,
    # and sometimes the closing parenthesis is split into a separate delta event.
    remove_parentheses: bool = False
    citation_regexp = re.compile(r"\(\[([^\]]+)\]\((https?:\/\/[^\)]+)\)")

    async for event in stream:
        LOGGER.debug("Received event: %s", event)

        if isinstance(event, ResponseOutputItemAddedEvent):
            if isinstance(event.item, ResponseFunctionToolCall):
                # OpenAI has tool calls as individual events
                # while HA puts tool calls inside the assistant message.
                # We turn them into individual assistant content for HA
                # to ensure that tools are called as soon as possible.
                yield {"role": "assistant"}
                last_role = "assistant"
                last_summary_index = None
                current_tool_call = event.item
            elif (
                isinstance(event.item, ResponseOutputMessage)
                or (
                    isinstance(event.item, ResponseReasoningItem)
                    and last_summary_index is not None
                )  # Subsequent ResponseReasoningItem
                or last_role != "assistant"
            ):
                yield {"role": "assistant"}
                last_role = "assistant"
                last_summary_index = None
        elif isinstance(event, ResponseOutputItemDoneEvent):
            if isinstance(event.item, ResponseReasoningItem):
                yield {
                    "native": ResponseReasoningItem(
                        type="reasoning",
                        id=event.item.id,
                        summary=[],  # Remove summaries
                        encrypted_content=event.item.encrypted_content,
                    )
                }
                last_summary_index = len(event.item.summary) - 1
            elif isinstance(event.item, ResponseCodeInterpreterToolCall):
                yield {
                    "tool_calls": [
                        llm.ToolInput(
                            id=event.item.id,
                            tool_name="code_interpreter",
                            tool_args={
                                "code": event.item.code,
                                "container": event.item.container_id,
                            },
                            external=True,
                        )
                    ]
                }
                yield {
                    "role": "tool_result",
                    "tool_call_id": event.item.id,
                    "tool_name": "code_interpreter",
                    "tool_result": {
                        "output": (
                            [output.to_dict() for output in event.item.outputs]  # type: ignore[misc]
                            if event.item.outputs is not None
                            else None
                        )
                    },
                }
                last_role = "tool_result"
            elif isinstance(event.item, ResponseFunctionWebSearch):
                yield {
                    "tool_calls": [
                        llm.ToolInput(
                            id=event.item.id,
                            tool_name="web_search_call",
                            tool_args={
                                "action": event.item.action.to_dict()
                                if event.item.action
                                else None,
                            },
                            external=True,
                        )
                    ]
                }
                yield {
                    "role": "tool_result",
                    "tool_call_id": event.item.id,
                    "tool_name": "web_search_call",
                    "tool_result": {"status": event.item.status},
                }
                last_role = "tool_result"
            elif isinstance(event.item, ImageGenerationCall):
                if last_summary_index is not None:
                    yield {"role": "assistant"}
                    last_role = "assistant"
                    last_summary_index = None
                yield {"native": event.item}
                last_summary_index = -1  # Trigger new assistant message on next turn
        elif isinstance(event, ResponseTextDeltaEvent):
            data = event.delta
            if remove_parentheses:
                data = data.removeprefix(")")
                remove_parentheses = False
            elif remove_citations and (match := citation_regexp.search(data)):
                match_start, match_end = match.span()
                # remove leading space if any
                if data[match_start - 1 : match_start] == " ":
                    match_start -= 1
                # remove closing parenthesis:
                if data[match_end : match_end + 1] == ")":
                    match_end += 1
                else:
                    remove_parentheses = True
                data = data[:match_start] + data[match_end:]
            if data:
                yield {"content": data}
        elif isinstance(event, ResponseReasoningSummaryTextDeltaEvent):
            # OpenAI can output several reasoning summaries
            # in a single ResponseReasoningItem. We split them as separate
            # AssistantContent messages. Only last of them will have
            # the reasoning `native` field set.
            if (
                last_summary_index is not None
                and event.summary_index != last_summary_index
            ):
                yield {"role": "assistant"}
                last_role = "assistant"
            last_summary_index = event.summary_index
            yield {"thinking_content": event.delta}
        elif isinstance(event, ResponseFunctionCallArgumentsDeltaEvent):
            current_tool_call.arguments += event.delta
        elif isinstance(event, ResponseFunctionCallArgumentsDoneEvent):
            current_tool_call.status = "completed"
            yield {
                "tool_calls": [
                    llm.ToolInput(
                        id=current_tool_call.call_id,
                        tool_name=current_tool_call.name,
                        tool_args=json.loads(current_tool_call.arguments),
                    )
                ]
            }
        elif isinstance(event, ResponseCompletedEvent):
            if event.response.usage is not None:
                chat_log.async_trace(
                    {
                        "stats": {
                            "input_tokens": event.response.usage.input_tokens,
                            "output_tokens": event.response.usage.output_tokens,
                        }
                    }
                )
        elif isinstance(event, ResponseIncompleteEvent):
            if event.response.usage is not None:
                chat_log.async_trace(
                    {
                        "stats": {
                            "input_tokens": event.response.usage.input_tokens,
                            "output_tokens": event.response.usage.output_tokens,
                        }
                    }
                )

            if (
                event.response.incomplete_details
                and event.response.incomplete_details.reason
            ):
                reason: str = event.response.incomplete_details.reason
            else:
                reason = "unknown reason"

            if reason == "max_output_tokens":
                reason = "max output tokens reached"
            elif reason == "content_filter":
                reason = "content filter triggered"

            raise HomeAssistantError(f"OpenAI response incomplete: {reason}")
        elif isinstance(event, ResponseFailedEvent):
            if event.response.usage is not None:
                chat_log.async_trace(
                    {
                        "stats": {
                            "input_tokens": event.response.usage.input_tokens,
                            "output_tokens": event.response.usage.output_tokens,
                        }
                    }
                )
            reason = "unknown reason"
            if event.response.error is not None:
                reason = event.response.error.message
            raise HomeAssistantError(f"OpenAI response failed: {reason}")
        elif isinstance(event, ResponseErrorEvent):
            raise HomeAssistantError(f"OpenAI response error: {event.message}")