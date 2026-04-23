async def delete_session_message(chat_id, session_id, msg_id):
    if not _ensure_owned_chat(chat_id):
        return get_json_result(data=False, message="No authorization.", code=RetCode.AUTHENTICATION_ERROR)
    try:
        ok, conv = ConversationService.get_by_id(session_id)
        if not ok or conv.dialog_id != chat_id:
            return get_data_error_result(message="Session not found!")
        conv = conv.to_dict()
        for i, msg in enumerate(conv["message"]):
            if msg_id != msg.get("id", ""):
                continue
            assert conv["message"][i + 1]["id"] == msg_id
            conv["message"].pop(i)
            conv["message"].pop(i)
            conv["reference"].pop(max(0, i // 2 - 1))
            break
        ConversationService.update_by_id(conv["id"], conv)
        return get_json_result(data=_build_session_response(conv))
    except Exception as ex:
        return server_error_response(ex)