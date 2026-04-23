def list_datasets(tenant_id: str, args: dict):
    """
    List datasets.

    :param tenant_id: tenant ID
    :param args: query arguments
    :return: (success, result) or (success, error_message)
    """
    kb_id = args.get("id")
    name = args.get("name")
    page = int(args.get("page", 1))
    page_size = int(args.get("page_size", 30))
    ext_fields = args.get("ext", {})
    parser_id = ext_fields.get("parser_id")
    keywords = ext_fields.get("keywords", "")
    orderby = args.get("orderby", "create_time")
    desc_arg = args.get("desc", "true")
    if isinstance(desc_arg, str):
        desc = desc_arg.lower() != "false"
    elif isinstance(desc_arg, bool):
        desc = desc_arg
    else:
        # unknown type, default to True
        desc = True

    if kb_id:
        kbs = KnowledgebaseService.get_kb_by_id(kb_id, tenant_id)
        if not kbs:
            return False, f"User '{tenant_id}' lacks permission for dataset '{kb_id}'"
    if name:
        kbs = KnowledgebaseService.get_kb_by_name(name, tenant_id)
        if not kbs:
            return False, f"User '{tenant_id}' lacks permission for dataset '{name}'"
    if ext_fields.get("owner_ids", []):
        tenant_ids = ext_fields["owner_ids"]
    else:
        tenants = TenantService.get_joined_tenants_by_user_id(tenant_id)
        tenant_ids = [m["tenant_id"] for m in tenants]
    kbs, total = KnowledgebaseService.get_list(
        tenant_ids,
        tenant_id,
        page,
        page_size,
        orderby,
        desc,
        kb_id,
        name,
        keywords,
        parser_id
    )
    users = UserService.get_by_ids([m["tenant_id"] for m in kbs])
    user_map = {m.id: m.to_dict() for m in users}
    response_data_list = []
    for kb in kbs:
        user_dict = user_map.get(kb["tenant_id"], {})
        kb.update({
            "nickname": user_dict.get("nickname", ""),
            "tenant_avatar": user_dict.get("avatar", "")
        })
        response_data_list.append(remap_dictionary_keys(kb))
    return True, {"data": response_data_list, "total": total}