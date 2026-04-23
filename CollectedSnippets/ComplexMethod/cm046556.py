async def _anthropic_passthrough_non_streaming(
    llama_backend,
    openai_messages,
    openai_tools,
    temperature,
    top_p,
    top_k,
    max_tokens,
    message_id,
    model_name,
    stop = None,
    min_p = None,
    repetition_penalty = None,
    presence_penalty = None,
    tool_choice = "auto",
):
    """Non-streaming client-side pass-through."""
    target_url = f"{llama_backend.base_url}/v1/chat/completions"
    body = _build_passthrough_payload(
        openai_messages,
        openai_tools,
        temperature,
        top_p,
        top_k,
        max_tokens,
        False,
        stop = stop,
        min_p = min_p,
        repetition_penalty = repetition_penalty,
        presence_penalty = presence_penalty,
        tool_choice = tool_choice,
    )

    async with httpx.AsyncClient() as client:
        resp = await client.post(target_url, json = body, timeout = 600)

    if resp.status_code != 200:
        raise HTTPException(
            status_code = resp.status_code,
            detail = f"llama-server error: {resp.text[:500]}",
        )

    data = resp.json()
    choice = (data.get("choices") or [{}])[0]
    message = choice.get("message") or {}
    finish_reason = choice.get("finish_reason")

    content_blocks = []
    text = message.get("content") or ""
    if text:
        text = _TOOL_XML_RE.sub("", text).strip()
        if text:
            content_blocks.append(AnthropicResponseTextBlock(text = text))

    tool_calls = message.get("tool_calls") or []
    for tc in tool_calls:
        fn = tc.get("function") or {}
        try:
            args = json.loads(fn.get("arguments", "{}"))
        except json.JSONDecodeError:
            args = {}
        content_blocks.append(
            AnthropicResponseToolUseBlock(
                id = tc.get("id", ""),
                name = fn.get("name", ""),
                input = args,
            )
        )

    if tool_calls:
        stop_reason = "tool_use"
    elif finish_reason == "length":
        stop_reason = "max_tokens"
    else:
        stop_reason = "end_turn"

    usage = data.get("usage") or {}
    resp_obj = AnthropicMessagesResponse(
        id = message_id,
        model = model_name,
        content = content_blocks,
        stop_reason = stop_reason,
        usage = AnthropicUsage(
            input_tokens = usage.get("prompt_tokens", 0),
            output_tokens = usage.get("completion_tokens", 0),
        ),
    )
    return JSONResponse(content = resp_obj.model_dump())