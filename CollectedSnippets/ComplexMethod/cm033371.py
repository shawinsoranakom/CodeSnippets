async def agents_completion_openai_compatibility(tenant_id, agent_id):
    req = await get_request_json()
    messages = req.get("messages", [])
    if not messages:
        return get_error_data_result("You must provide at least one message.")
    if not UserCanvasService.query(user_id=tenant_id, id=agent_id):
        return get_error_data_result(f"You don't own the agent {agent_id}")

    filtered_messages = [m for m in messages if m["role"] in ["user", "assistant"]]
    prompt_tokens = sum(num_tokens_from_string(m["content"]) for m in filtered_messages)
    if not filtered_messages:
        return jsonify(
            get_data_openai(
                id=agent_id,
                content="No valid messages found (user or assistant).",
                finish_reason="stop",
                model=req.get("model", ""),
                completion_tokens=num_tokens_from_string("No valid messages found (user or assistant)."),
                prompt_tokens=prompt_tokens,
            )
        )

    question = next((m["content"] for m in reversed(messages) if m["role"] == "user"), "")

    stream = req.pop("stream", False)
    if stream:
        resp = Response(
            completion_openai(
                tenant_id,
                agent_id,
                question,
                session_id=req.pop("session_id", req.get("id", "")) or req.get("metadata", {}).get("id", ""),
                stream=True,
                **req,
            ),
            mimetype="text/event-stream",
        )
        resp.headers.add_header("Cache-control", "no-cache")
        resp.headers.add_header("Connection", "keep-alive")
        resp.headers.add_header("X-Accel-Buffering", "no")
        resp.headers.add_header("Content-Type", "text/event-stream; charset=utf-8")
        return resp
    else:
        # For non-streaming, just return the response directly
        async for response in completion_openai(
                tenant_id,
                agent_id,
                question,
                session_id=req.pop("session_id", req.get("id", "")) or req.get("metadata", {}).get("id", ""),
                stream=False,
                **req,
            ):
            return jsonify(response)

        return None