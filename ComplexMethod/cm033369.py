async def chat_completion(tenant_id, chat_id):
    req = await get_request_json()
    if not req:
        req = {"question": ""}
    if not req.get("session_id"):
        req["question"] = ""
    dia = DialogService.query(tenant_id=tenant_id, id=chat_id, status=StatusEnum.VALID.value)
    if not dia:
        return get_error_data_result(f"You don't own the chat {chat_id}")
    dia = dia[0]
    if req.get("session_id"):
        if not ConversationService.query(id=req["session_id"], dialog_id=chat_id):
            return get_error_data_result(f"You don't own the session {req['session_id']}")

    metadata_condition = req.get("metadata_condition") or {}
    if metadata_condition and not isinstance(metadata_condition, dict):
        return get_error_data_result(message="metadata_condition must be an object.")

    if metadata_condition and req.get("question"):
        metas = DocMetadataService.get_flatted_meta_by_kbs(dia.kb_ids or [])
        filtered_doc_ids = meta_filter(
            metas,
            convert_conditions(metadata_condition),
            metadata_condition.get("logic", "and"),
        )
        if metadata_condition.get("conditions") and not filtered_doc_ids:
            filtered_doc_ids = ["-999"]

        if filtered_doc_ids:
            req["doc_ids"] = ",".join(filtered_doc_ids)
        else:
            req.pop("doc_ids", None)

    if req.get("stream", True):
        resp = Response(rag_completion(tenant_id, chat_id, **req), mimetype="text/event-stream")
        resp.headers.add_header("Cache-control", "no-cache")
        resp.headers.add_header("Connection", "keep-alive")
        resp.headers.add_header("X-Accel-Buffering", "no")
        resp.headers.add_header("Content-Type", "text/event-stream; charset=utf-8")

        return resp
    else:
        answer = None
        async for ans in rag_completion(tenant_id, chat_id, **req):
            answer = ans
            break
        return get_result(data=answer)