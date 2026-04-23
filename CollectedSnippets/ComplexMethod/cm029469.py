async def _parse_chunk(
    chunk: types.GenerateContentResponse,
    state: GeminiParseState,
    on_event: EventSink,
) -> None:
    if not chunk.candidates:
        return

    candidate_content = chunk.candidates[0].content
    if not candidate_content or not candidate_content.parts:
        return

    if candidate_content.role:
        state.model_role = candidate_content.role

    for part in candidate_content.parts:
        # Preserve each model part as streamed so thought signatures remain attached.
        state.model_parts.append(part)

        if getattr(part, "thought", False) and part.text:
            await on_event(StreamEvent(type="thinking_delta", text=part.text))
            continue

        if part.function_call:
            args = part.function_call.args or {}
            tool_id = part.function_call.id or f"tool-{uuid.uuid4().hex[:6]}"
            tool_name = part.function_call.name or "unknown_tool"

            await on_event(
                StreamEvent(
                    type="tool_call_delta",
                    tool_call_id=tool_id,
                    tool_name=tool_name,
                    tool_arguments=args,
                )
            )

            state.tool_calls.append(
                ToolCall(
                    id=tool_id,
                    name=tool_name,
                    arguments=args,
                )
            )
            continue

        if part.text:
            state.assistant_text += part.text
            await on_event(StreamEvent(type="assistant_delta", text=part.text))