async def get_session(chat_id, session_id):
    if not _ensure_owned_chat(chat_id):
        return get_json_result(data=False, message="No authorization.", code=RetCode.AUTHENTICATION_ERROR)
    try:
        ok, conv = ConversationService.get_by_id(session_id)
        if not ok:
            return get_data_error_result(message="Session not found!")
        if conv.dialog_id != chat_id:
            return get_data_error_result(message="Session does not belong to this chat!")
        dialog = _ensure_owned_chat(chat_id)
        avatar = dialog[0].icon if dialog else ""
        for ref in conv.reference:
            if isinstance(ref, list):
                continue
            ref["chunks"] = chunks_format(ref)
        result = _build_session_response(conv.to_dict())
        result["avatar"] = avatar
        return get_json_result(data=result)
    except Exception as ex:
        return server_error_response(ex)