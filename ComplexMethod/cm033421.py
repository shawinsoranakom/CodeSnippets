async def delete_sessions(chat_id):
    if not _ensure_owned_chat(chat_id):
        return get_json_result(data=False, message="No authorization.", code=RetCode.AUTHENTICATION_ERROR)
    try:
        req = await get_request_json()
        if not req:
            return get_json_result(data={})

        session_ids = req.get("ids")
        if not session_ids:
            if req.get("delete_all") is True:
                session_ids = [conv.id for conv in ConversationService.query(dialog_id=chat_id)]
                if not session_ids:
                    return get_json_result(data={})
            else:
                return get_json_result(data={})
        unique_ids, duplicate_messages = check_duplicate_ids(session_ids, "session")
        errors = []
        success_count = 0
        for sid in unique_ids:
            if not ConversationService.query(id=sid, dialog_id=chat_id):
                errors.append(f"The chat doesn't own the session {sid}")
                continue
            ConversationService.delete_by_id(sid)
            success_count += 1
        all_errors = errors + duplicate_messages
        if all_errors:
            if success_count > 0:
                return get_json_result(
                    data={"success_count": success_count, "errors": all_errors},
                    message=f"Partially deleted {success_count} sessions with {len(all_errors)} errors",
                )
            return get_data_error_result(message="; ".join(all_errors))
        return get_json_result(data=True)
    except Exception as ex:
        return server_error_response(ex)