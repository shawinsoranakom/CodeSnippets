async def bulk_delete_chats():
    req = await get_request_json()
    if not req:
        return get_json_result(data={})

    ids = req.get("ids")
    if not ids:
        if req.get("delete_all") is True:
            ids = [
                chat.id
                for chat in DialogService.query(
                    tenant_id=current_user.id, status=StatusEnum.VALID.value
                )
            ]
            if not ids:
                return get_json_result(data={})
        else:
            return get_json_result(data={})

    errors = []
    success_count = 0
    unique_ids, duplicate_messages = check_duplicate_ids(ids, "chat")

    for chat_id in unique_ids:
        if not _ensure_owned_chat(chat_id):
            errors.append(f"Chat({chat_id}) not found.")
            continue
        success_count += DialogService.update_by_id(chat_id, {"status": StatusEnum.INVALID.value})

    all_errors = errors + duplicate_messages
    if all_errors:
        if success_count > 0:
            return get_json_result(
                data={"success_count": success_count, "errors": all_errors},
                message=f"Partially deleted {success_count} chats with {len(all_errors)} errors",
            )
        return get_data_error_result(message="; ".join(all_errors))

    return get_json_result(data={"success_count": success_count})