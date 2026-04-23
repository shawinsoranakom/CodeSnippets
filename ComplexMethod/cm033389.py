async def list_memory(filter_params: dict, keywords: str, page: int=1, page_size: int = 50):
    """
    :param filter_params: {
        "memory_type": list[str],
        "tenant_id": list[str],
        "storage_type": str
    }
    :param keywords: str
    :param page: int
    :param page_size: int
    """
    filter_dict: dict = {"storage_type": filter_params.get("storage_type")}
    tenant_ids = filter_params.get("tenant_id")
    if not filter_params.get("tenant_id"):
        # restrict to current user's tenants
        user_tenants = UserTenantService.get_user_tenant_relation_by_user_id(current_user.id)
        filter_dict["tenant_id"] = [tenant["tenant_id"] for tenant in user_tenants]
    else:
        if len(tenant_ids) == 1 and ',' in tenant_ids[0]:
            tenant_ids = tenant_ids[0].split(',')
        filter_dict["tenant_id"] = tenant_ids
    memory_types = filter_params.get("memory_type")
    if memory_types and len(memory_types) == 1 and ',' in memory_types[0]:
        memory_types = memory_types[0].split(',')
    filter_dict["memory_type"] = memory_types

    memory_list, count = MemoryService.get_by_filter(filter_dict, keywords, page, page_size)
    [memory.update({"memory_type": get_memory_type_human(memory["memory_type"])}) for memory in memory_list]
    return {
        "memory_list": memory_list, "total_count": count
    }