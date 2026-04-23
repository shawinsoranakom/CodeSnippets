async def session_completion():
    req = await get_request_json()
    msg = []
    for m in req["messages"]:
        if m["role"] == "system":
            continue
        if m["role"] == "assistant" and not msg:
            continue
        msg.append(m)
    message_id = msg[-1].get("id") if msg else None
    chat_id = req.pop("chat_id", "") or ""
    session_id = req.pop("session_id", "") or ""
    chat_model_id = req.pop("llm_id", "")

    chat_model_config = {}
    for model_config in ["temperature", "top_p", "frequency_penalty", "presence_penalty", "max_tokens"]:
        config = req.get(model_config)
        if config:
            chat_model_config[model_config] = config

    try:
        conv = None
        if session_id and not chat_id:
            return get_data_error_result(message="`chat_id` is required when `session_id` is provided.")

        if chat_id:
            if not _ensure_owned_chat(chat_id):
                return get_json_result(
                    data=False,
                    message="No authorization.",
                    code=RetCode.AUTHENTICATION_ERROR,
                )
            e, dia = DialogService.get_by_id(chat_id)
            if not e:
                return get_data_error_result(message="Chat not found!")
            if session_id:
                e, conv = ConversationService.get_by_id(session_id)
                if not e:
                    return get_data_error_result(message="Session not found!")
                if conv.dialog_id != chat_id:
                    return get_data_error_result(message="Session does not belong to this chat!")
            else:
                conv = _create_session_for_completion(chat_id, dia, req.get("user_id", current_user.id))
                session_id = conv.id
            conv.message = deepcopy(req["messages"])
        else:
            dia = _build_default_completion_dialog()
            dia.llm_setting = chat_model_config

        del req["messages"]

        if conv is not None:
            if not conv.reference:
                conv.reference = []
            conv.reference = [r for r in conv.reference if r]
            conv.reference.append({"chunks": [], "doc_aggs": []})

        if chat_model_id:
            if not TenantLLMService.get_api_key(tenant_id=dia.tenant_id, model_name=chat_model_id):
                return get_data_error_result(message=f"Cannot use specified model {chat_model_id}.")
            dia.llm_id = chat_model_id
            dia.llm_setting = chat_model_config

        stream_mode = req.pop("stream", True)

        def _format_answer(ans):
            formatted = structure_answer(conv, ans, message_id, session_id)
            if chat_id:
                formatted["chat_id"] = chat_id
            return formatted

        async def stream():
            nonlocal dia, msg, req, conv
            try:
                async for ans in async_chat(dia, msg, True, **req):
                    ans = _format_answer(ans)
                    yield "data:" + json.dumps({"code": 0, "message": "", "data": ans}, ensure_ascii=False) + "\n\n"
                if conv is not None:
                    ConversationService.update_by_id(conv.id, conv.to_dict())
            except Exception as ex:
                logging.exception(ex)
                yield "data:" + json.dumps({"code": 500, "message": str(ex), "data": {"answer": "**ERROR**: " + str(ex), "reference": []}}, ensure_ascii=False) + "\n\n"
            yield "data:" + json.dumps({"code": 0, "message": "", "data": True}, ensure_ascii=False) + "\n\n"

        if stream_mode:
            resp = Response(stream(), mimetype="text/event-stream")
            resp.headers.add_header("Cache-control", "no-cache")
            resp.headers.add_header("Connection", "keep-alive")
            resp.headers.add_header("X-Accel-Buffering", "no")
            resp.headers.add_header("Content-Type", "text/event-stream; charset=utf-8")
            return resp

        answer = None
        async for ans in async_chat(dia, msg, **req):
            answer = _format_answer(ans)
            if conv is not None:
                ConversationService.update_by_id(conv.id, conv.to_dict())
            break
        return get_json_result(data=answer)
    except Exception as ex:
        return server_error_response(ex)