async def _responses_non_streaming(
    payload: ResponsesRequest,
    messages: list[ChatMessage],
    request: Request,
) -> JSONResponse:
    """Handle a non-streaming Responses API call."""
    chat_req = _build_chat_request(payload, messages, stream = False)
    result = await openai_chat_completions(chat_req, request)

    # openai_chat_completions returns a JSONResponse for non-streaming
    if isinstance(result, JSONResponse):
        body = json.loads(result.body.decode())
    elif isinstance(result, Response):
        body = json.loads(result.body.decode())
    else:
        body = result

    choices = body.get("choices", [])
    text = ""
    tool_calls: list[dict] = []
    if choices:
        msg = choices[0].get("message", {}) or {}
        text = msg.get("content", "") or ""
        tool_calls = msg.get("tool_calls") or []

    usage_data = body.get("usage", {})
    input_tokens = usage_data.get("prompt_tokens", 0)
    output_tokens = usage_data.get("completion_tokens", 0)

    resp_id = f"resp_{uuid.uuid4().hex[:12]}"

    # Responses API emits each tool call as its own top-level output item,
    # alongside an optional assistant text message. Emit the text message
    # only when the model actually produced content, so clients that expect
    # a pure tool-call turn (finish_reason="tool_calls") don't see a spurious
    # empty message item.
    output_items: list[dict] = []
    if text:
        msg_id = f"msg_{uuid.uuid4().hex[:12]}"
        output_items.append(
            ResponsesOutputMessage(
                id = msg_id,
                status = "completed",
                role = "assistant",
                content = [ResponsesOutputTextContent(text = text)],
            ).model_dump()
        )
    output_items.extend(_chat_tool_calls_to_responses_output(tool_calls))

    response = ResponsesResponse(
        id = resp_id,
        created_at = int(time.time()),
        status = "completed",
        model = body.get("model", payload.model),
        output = output_items,
        usage = ResponsesUsage(
            input_tokens = input_tokens,
            output_tokens = output_tokens,
            total_tokens = input_tokens + output_tokens,
        ),
        temperature = payload.temperature,
        top_p = payload.top_p,
        max_output_tokens = payload.max_output_tokens,
        instructions = payload.instructions,
    )
    return JSONResponse(content = response.model_dump())