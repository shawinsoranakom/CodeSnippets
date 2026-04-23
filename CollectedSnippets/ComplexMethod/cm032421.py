def stream_chat_completion(
    client: HttpClient,
    chat_id: str,
    model: str,
    messages: List[Dict[str, Any]],
    extra_body: Optional[Dict[str, Any]] = None,
) -> ChatSample:
    payload: Dict[str, Any] = {"model": model, "messages": messages, "stream": True}
    if extra_body:
        payload["extra_body"] = extra_body
    t0 = time.perf_counter()
    response = client.request(
        "POST",
        f"/chats_openai/{chat_id}/chat/completions",
        json_body=payload,
        stream=True,
    )
    error = _parse_stream_error(response)
    if error:
        response.close()
        return ChatSample(t0=t0, t1=None, t2=None, error=error)

    t1: Optional[float] = None
    t2: Optional[float] = None
    stream_error: Optional[str] = None
    content_parts: List[str] = []
    try:
        for raw_line in response.iter_lines(decode_unicode=True):
            if raw_line is None:
                continue
            line = raw_line.strip()
            if not line or not line.startswith("data:"):
                continue
            data = line[5:].strip()
            if not data:
                continue
            if data == "[DONE]":
                t2 = time.perf_counter()
                break
            try:
                chunk = json.loads(data)
            except Exception as exc:
                stream_error = f"Invalid JSON chunk: {exc}"
                t2 = time.perf_counter()
                break
            choices = chunk.get("choices") or []
            choice = choices[0] if choices else {}
            delta = choice.get("delta") or {}
            content = delta.get("content")
            if t1 is None and isinstance(content, str) and content != "":
                t1 = time.perf_counter()
            if isinstance(content, str) and content:
                content_parts.append(content)
            finish_reason = choice.get("finish_reason")
            if finish_reason:
                t2 = time.perf_counter()
                break
    finally:
        response.close()

    if t2 is None:
        t2 = time.perf_counter()
    response_text = "".join(content_parts) if content_parts else None
    if stream_error:
        return ChatSample(t0=t0, t1=t1, t2=t2, error=stream_error, response_text=response_text)
    if t1 is None:
        return ChatSample(t0=t0, t1=None, t2=t2, error="No assistant content received", response_text=response_text)
    return ChatSample(t0=t0, t1=t1, t2=t2, error=None, response_text=response_text)