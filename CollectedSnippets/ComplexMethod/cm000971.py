def _append_gap_to_builder(
    gap: list[ChatMessage],
    builder: TranscriptBuilder,
) -> None:
    """Append gap messages from chat-db into the TranscriptBuilder.

    Converts ChatMessage (OpenAI format) to TranscriptBuilder entries
    (Claude CLI JSONL format) so the uploaded transcript covers all turns.

    Pre-condition: ``gap`` always starts at a user or assistant boundary
    (never mid-turn at a ``tool`` role), because ``detect_gap`` enforces
    ``session_messages[wm-1].role == 'assistant'`` before returning a non-empty
    gap.  Any ``tool`` role messages within the gap always follow an assistant
    entry that already exists in the builder or in the gap itself.
    """
    for msg in gap:
        if msg.role == "user":
            builder.append_user(msg.content or "")
        elif msg.role == "assistant":
            content_blocks: list[dict] = []
            if msg.content:
                content_blocks.append({"type": "text", "text": msg.content})
            if msg.tool_calls:
                for tc in msg.tool_calls:
                    fn = tc.get("function", {}) if isinstance(tc, dict) else {}
                    input_data = util_json.loads(fn.get("arguments", "{}"), fallback={})
                    content_blocks.append(
                        {
                            "type": "tool_use",
                            "id": tc.get("id", "") if isinstance(tc, dict) else "",
                            "name": fn.get("name", "unknown"),
                            "input": input_data,
                        }
                    )
            if not content_blocks:
                # Fallback: ensure every assistant gap message produces an entry
                # so the builder's entry count matches the gap length.
                content_blocks.append({"type": "text", "text": ""})
            builder.append_assistant(content_blocks=content_blocks)
        elif msg.role == "tool":
            if msg.tool_call_id:
                builder.append_tool_result(
                    tool_use_id=msg.tool_call_id,
                    content=msg.content or "",
                )
            else:
                # Malformed tool message — no tool_call_id to link to an
                # assistant tool_use block.  Skip to avoid an unmatched
                # tool_result entry in the builder (which would confuse --resume).
                logger.warning(
                    "[Baseline] Skipping tool gap message with no tool_call_id"
                )