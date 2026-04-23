def list_chats():
    chat_id = request.args.get("id")
    name = request.args.get("name")
    keywords = request.args.get("keywords", "")
    orderby = request.args.get("orderby", "create_time")
    desc = request.args.get("desc", "true").lower() != "false"
    owner_ids = request.args.getlist("owner_ids")
    exact_filters = {"id": chat_id, "name": name}
    if chat_id or name:
        keywords = ""

    try:
        page_number = int(request.args.get("page", 0))
        items_per_page = int(request.args.get("page_size", 0))

        if owner_ids:
            chats, total = DialogService.get_by_tenant_ids(
                owner_ids, current_user.id, 0, 0, orderby, desc, keywords, **exact_filters
            )
            chats = [chat for chat in chats if chat["tenant_id"] in owner_ids]
            total = len(chats)
            if page_number and items_per_page:
                start = (page_number - 1) * items_per_page
                chats = chats[start : start + items_per_page]
        else:
            chats, total = DialogService.get_by_tenant_ids(
                [], current_user.id, page_number, items_per_page, orderby, desc, keywords, **exact_filters
            )

        return get_json_result(
            data={"chats": [_build_chat_response(chat) for chat in chats], "total": total}
        )
    except Exception as ex:
        return server_error_response(ex)