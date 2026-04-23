def _record_turn_to_transcript(
    response: LLMLoopResponse,
    tool_results: list[ToolCallResult] | None,
    *,
    transcript_builder: TranscriptBuilder,
    model: str,
) -> None:
    """Append assistant + tool-result entries to the transcript builder.

    Kept separate from :func:`_mutate_openai_messages` so the two
    concerns (next-LLM-call payload vs. durable conversation log) can
    evolve independently.
    """
    if tool_results:
        content_blocks: list[dict[str, Any]] = []
        if response.response_text:
            content_blocks.append({"type": "text", "text": response.response_text})
        for tc in response.tool_calls:
            try:
                args = orjson.loads(tc.arguments) if tc.arguments else {}
            except (ValueError, TypeError, orjson.JSONDecodeError) as parse_err:
                logger.debug(
                    "[Baseline] Failed to parse tool_call arguments "
                    "(tool=%s, id=%s): %s",
                    tc.name,
                    tc.id,
                    parse_err,
                )
                args = {}
            content_blocks.append(
                {
                    "type": "tool_use",
                    "id": tc.id,
                    "name": tc.name,
                    "input": args,
                }
            )
        if content_blocks:
            transcript_builder.append_assistant(
                content_blocks=content_blocks,
                model=model,
                stop_reason=STOP_REASON_TOOL_USE,
            )
        for tr in tool_results:
            # Record tool result to transcript AFTER the assistant tool_use
            # block to maintain correct Anthropic API ordering:
            # assistant(tool_use) → user(tool_result)
            transcript_builder.append_tool_result(
                tool_use_id=tr.tool_call_id,
                content=tr.content,
            )
    elif response.response_text:
        transcript_builder.append_assistant(
            content_blocks=[{"type": "text", "text": response.response_text}],
            model=model,
            stop_reason=STOP_REASON_END_TURN,
        )