async def _transform_stream(  # noqa: C901 - This is complex, but better to have it in one place
    chat_log: conversation.ChatLog,
    stream: Any,
    remove_citations: bool = False,
) -> AsyncGenerator[
    conversation.AssistantContentDeltaDict | conversation.ToolResultContentDeltaDict
]:
    """Transform stream result into HA format."""
    last_summary_index = None
    last_role: Literal["assistant", "tool_result"] | None = None
    current_tool_call: LLMResponseFunctionCallOutputItem | None = None

    # Non-reasoning models don't follow our request to remove citations, so we remove
    # them manually here. They always follow the same pattern: the citation is always
    # in parentheses in Markdown format, the citation is always in a single delta event,
    # and sometimes the closing parenthesis is split into a separate delta event.
    remove_parentheses: bool = False
    citation_regexp = re.compile(r"\(\[([^\]]+)\]\((https?:\/\/[^\)]+)\)")

    async for event in stream:
        _LOGGER.debug("Event[%s]", getattr(event, "type", None))

        if isinstance(event, LLMResponseOutputItemAddedEvent):
            if isinstance(event.item, LLMResponseFunctionCallOutputItem):
                # OpenAI has tool calls as individual events
                # while HA puts tool calls inside the assistant message.
                # We turn them into individual assistant content for HA
                # to ensure that tools are called as soon as possible.
                yield {"role": "assistant"}
                last_role = "assistant"
                last_summary_index = None
                current_tool_call = event.item
            elif (
                isinstance(event.item, LLMResponseMessageOutputItem)
                or (
                    isinstance(event.item, LLMResponseReasoningOutputItem)
                    and last_summary_index is not None
                )  # Subsequent ResponseReasoningItem
                or last_role != "assistant"
            ):
                yield {"role": "assistant"}
                last_role = "assistant"
                last_summary_index = None

        elif isinstance(event, LLMResponseOutputItemDoneEvent):
            if isinstance(event.item, LLMResponseReasoningOutputItem):
                encrypted_content = event.item.encrypted_content
                summary = event.item.summary

                yield {
                    "native": LLMResponseReasoningOutputItem(
                        type=event.item.type,
                        id=event.item.id,
                        summary=[],
                        encrypted_content=encrypted_content,
                    )
                }

                last_summary_index = len(summary) - 1 if summary else None
            elif isinstance(event.item, LLMResponseWebSearchCallOutputItem):
                action_dict = event.item.action
                yield {
                    "tool_calls": [
                        llm.ToolInput(
                            id=event.item.id,
                            tool_name="web_search_call",
                            tool_args={"action": action_dict},
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
            elif isinstance(event.item, LLMResponseImageOutputItem):
                yield {"native": event.item.raw}
                last_summary_index = -1  # Trigger new assistant message on next turn

        elif isinstance(event, LLMResponseOutputTextDeltaEvent):
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

        elif isinstance(event, LLMResponseReasoningSummaryTextDeltaEvent):
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

        elif isinstance(event, LLMResponseFunctionCallArgumentsDeltaEvent):
            if current_tool_call is not None:
                current_tool_call.arguments += event.delta

        elif isinstance(event, LLMResponseWebSearchCallSearchingEvent):
            yield {"role": "assistant"}

        elif isinstance(event, LLMResponseFunctionCallArgumentsDoneEvent):
            if current_tool_call is not None:
                current_tool_call.status = "completed"

                raw_args = json.loads(current_tool_call.arguments)
                for key in ("area", "floor"):
                    if key in raw_args and not raw_args[key]:
                        # Remove keys that are "" or None
                        raw_args.pop(key, None)

                yield {
                    "tool_calls": [
                        llm.ToolInput(
                            id=current_tool_call.call_id,
                            tool_name=current_tool_call.name,
                            tool_args=raw_args,
                        )
                    ]
                }

        elif isinstance(event, LLMResponseCompletedEvent):
            response = event.response
            if response and "usage" in response:
                usage = response["usage"]
                chat_log.async_trace(
                    {
                        "stats": {
                            "input_tokens": usage.get("input_tokens"),
                            "output_tokens": usage.get("output_tokens"),
                        }
                    }
                )

        elif isinstance(event, LLMResponseIncompleteEvent):
            response = event.response
            if response and "usage" in response:
                usage = response["usage"]
                chat_log.async_trace(
                    {
                        "stats": {
                            "input_tokens": usage.get("input_tokens"),
                            "output_tokens": usage.get("output_tokens"),
                        }
                    }
                )

            incomplete_details = response.get("incomplete_details")
            reason = "unknown reason"
            if incomplete_details is not None and incomplete_details.get("reason"):
                reason = incomplete_details["reason"]

            if reason == "max_output_tokens":
                reason = "max output tokens reached"
            elif reason == "content_filter":
                reason = "content filter triggered"

            raise HomeAssistantError(f"OpenAI response incomplete: {reason}")

        elif isinstance(event, LLMResponseFailedEvent):
            response = event.response
            if response and "usage" in response:
                usage = response["usage"]
                chat_log.async_trace(
                    {
                        "stats": {
                            "input_tokens": usage.get("input_tokens"),
                            "output_tokens": usage.get("output_tokens"),
                        }
                    }
                )
            reason = "unknown reason"
            if isinstance(error := response.get("error"), dict):
                reason = error.get("message") or reason
            raise HomeAssistantError(f"OpenAI response failed: {reason}")

        elif isinstance(event, LLMResponseErrorEvent):
            raise HomeAssistantError(f"OpenAI response error: {event.message}")