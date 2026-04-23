async def delete_agent_session(tenant_id, agent_id):
    errors = []
    success_count = 0
    req = await get_request_json()
    cvs = UserCanvasService.query(user_id=tenant_id, id=agent_id)
    if not cvs:
        return get_error_data_result(f"You don't own the agent {agent_id}")

    if not req:
        return get_result()

    ids = req.get("ids")
    if not ids:
        if req.get("delete_all") is True:
            ids = [conv.id for conv in API4ConversationService.query(dialog_id=agent_id)]
            if not ids:
                return get_result()
        else:
            return get_result()

    conv_list = ids

    unique_conv_ids, duplicate_messages = check_duplicate_ids(conv_list, "session")
    conv_list = unique_conv_ids

    for session_id in conv_list:
        conv = API4ConversationService.query(id=session_id, dialog_id=agent_id)
        if not conv:
            errors.append(f"The agent doesn't own the session {session_id}")
            continue
        API4ConversationService.delete_by_id(session_id)
        success_count += 1

    if errors:
        if success_count > 0:
            return get_result(data={"success_count": success_count, "errors": errors},
                              message=f"Partially deleted {success_count} sessions with {len(errors)} errors")
        else:
            return get_error_data_result(message="; ".join(errors))

    if duplicate_messages:
        if success_count > 0:
            return get_result(
                message=f"Partially deleted {success_count} sessions with {len(duplicate_messages)} errors",
                data={"success_count": success_count, "errors": duplicate_messages})
        else:
            return get_error_data_result(message=";".join(duplicate_messages))

    return get_result()