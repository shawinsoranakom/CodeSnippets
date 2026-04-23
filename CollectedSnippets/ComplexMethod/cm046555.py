async def _anthropic_tool_non_streaming(run_gen, message_id, model_name):
    """Non-streaming response for the tool-calling path.

    Builds ``content_blocks`` in generation order (text → tool_use → text →
    tool_use → ...), mirroring the streaming emitter's behavior. Deltas
    within a single synthesis turn are merged into the trailing text block;
    tool_use blocks interrupt the text sequence and open a new text block on
    the next content event.

    ``prev_text`` is reset on ``tool_end`` because
    ``generate_chat_completion_with_tools`` yields cumulative content *per
    turn* — the first content event of turn N+1 must diff against an empty
    baseline, not against turn N's final length.
    """
    content_blocks: list = []
    usage = {}
    prev_text = ""

    for event in run_gen():
        etype = event.get("type", "")
        if etype == "content":
            # Strip leaked tool-call XML
            clean = _TOOL_XML_RE.sub("", event["text"])
            new = clean[len(prev_text) :]
            prev_text = clean
            if new:
                if content_blocks and isinstance(
                    content_blocks[-1], AnthropicResponseTextBlock
                ):
                    content_blocks[-1].text += new
                else:
                    content_blocks.append(AnthropicResponseTextBlock(text = new))
        elif etype == "tool_start":
            content_blocks.append(
                AnthropicResponseToolUseBlock(
                    id = event["tool_call_id"],
                    name = event["tool_name"],
                    input = event.get("arguments", {}),
                )
            )
        elif etype == "tool_end":
            prev_text = ""
        elif etype == "metadata":
            usage = event.get("usage", {})

    resp = AnthropicMessagesResponse(
        id = message_id,
        model = model_name,
        content = content_blocks,
        stop_reason = "end_turn",
        usage = AnthropicUsage(
            input_tokens = usage.get("prompt_tokens", 0),
            output_tokens = usage.get("completion_tokens", 0),
        ),
    )
    return JSONResponse(content = resp.model_dump())