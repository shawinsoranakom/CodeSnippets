async def update_session(chat_id, session_id):
    if not _ensure_owned_chat(chat_id):
        return get_json_result(data=False, message="No authorization.", code=RetCode.AUTHENTICATION_ERROR)
    try:
        req = await get_request_json()
        if not ConversationService.query(id=session_id, dialog_id=chat_id):
            return get_data_error_result(message="Session not found!")
        if "message" in req or "messages" in req:
            return get_data_error_result(message="`messages` cannot be changed.")
        if "reference" in req:
            return get_data_error_result(message="`reference` cannot be changed.")
        name = req.get("name")
        if name is not None:
            if not isinstance(name, str) or not name.strip():
                return get_data_error_result(message="`name` can not be empty.")
            req["name"] = name.strip()[:255]
        update_fields = {k: v for k, v in req.items() if k not in {"id", "dialog_id", "chat_id", "user_id"}}
        if not ConversationService.update_by_id(session_id, update_fields):
            return get_data_error_result(message="Session not found!")
        ok, conv = ConversationService.get_by_id(session_id)
        if not ok:
            return get_data_error_result(message="Fail to update a session!")
        return get_json_result(data=_build_session_response(conv.to_dict()))
    except Exception as ex:
        return server_error_response(ex)