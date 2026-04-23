async def update_memory(memory_id: str, new_memory_setting: dict):
    """
    :param memory_id: str
    :param new_memory_setting: {
        "name": str,
        "permissions": str,
        "llm_id": str,
        "embd_id": str,
        "memory_type": list[str],
        "memory_size": int,
        "forgetting_policy": str,
        "temperature": float,
        "avatar": str,
        "description": str,
        "system_prompt": str,
        "user_prompt": str
    }
    """
    update_dict = {}
    # check name length
    if "name" in new_memory_setting:
        name = new_memory_setting["name"]
        memory_name = name.strip()
        if len(memory_name) == 0:
            raise ArgumentException("Memory name cannot be empty or whitespace.")
        if len(memory_name) > MEMORY_NAME_LIMIT:
            raise ArgumentException(f"Memory name '{memory_name}' exceeds limit of {MEMORY_NAME_LIMIT}.")
        update_dict["name"] = memory_name
    # check permissions valid
    if new_memory_setting.get("permissions"):
        if new_memory_setting["permissions"] not in [e.value for e in TenantPermission]:
            raise ArgumentException(f"Unknown permission '{new_memory_setting['permissions']}'.")
        update_dict["permissions"] = new_memory_setting["permissions"]
    if new_memory_setting.get("llm_id"):
        update_dict["llm_id"] = new_memory_setting["llm_id"]
    if new_memory_setting.get("embd_id"):
        update_dict["embd_id"] = new_memory_setting["embd_id"]
    if new_memory_setting.get("tenant_llm_id"):
        update_dict["tenant_llm_id"] = new_memory_setting["tenant_llm_id"]
    if new_memory_setting.get("tenant_embd_id"):
        update_dict["tenant_embd_id"] = new_memory_setting["tenant_embd_id"]
    if new_memory_setting.get("memory_type"):
        memory_type = set(new_memory_setting["memory_type"])
        invalid_type = memory_type - {e.name.lower() for e in MemoryType}
        if invalid_type:
            raise ArgumentException(f"Memory type '{invalid_type}' is not supported.")
        update_dict["memory_type"] = list(memory_type)
    # check memory_size valid
    if new_memory_setting.get("memory_size"):
        if not 0 < int(new_memory_setting["memory_size"]) <= MEMORY_SIZE_LIMIT:
            raise ArgumentException(f"Memory size should be in range (0, {MEMORY_SIZE_LIMIT}] Bytes.")
        update_dict["memory_size"] = new_memory_setting["memory_size"]
    # check forgetting_policy valid
    if new_memory_setting.get("forgetting_policy"):
        if new_memory_setting["forgetting_policy"] not in [e.value for e in ForgettingPolicy]:
            raise ArgumentException(f"Forgetting policy '{new_memory_setting['forgetting_policy']}' is not supported.")
        update_dict["forgetting_policy"] = new_memory_setting["forgetting_policy"]
    # check temperature valid
    if "temperature" in new_memory_setting:
        temperature = float(new_memory_setting["temperature"])
        if not 0 <= temperature <= 1:
            raise ArgumentException("Temperature should be in range [0, 1].")
        update_dict["temperature"] = temperature
    # allow update to empty fields
    for field in ["avatar", "description", "system_prompt", "user_prompt"]:
        if field in new_memory_setting:
            update_dict[field] = new_memory_setting[field]
    current_memory = MemoryService.get_by_memory_id(memory_id)
    if not current_memory:
        raise NotFoundException(f"Memory '{memory_id}' not found.")

    memory_dict = current_memory.to_dict()
    memory_dict.update({"memory_type": get_memory_type_human(current_memory.memory_type)})
    to_update = {}
    for k, v in update_dict.items():
        if isinstance(v, list) and set(memory_dict[k]) != set(v):
            to_update[k] = v
        elif memory_dict[k] != v:
            to_update[k] = v

    if not to_update:
        return True, memory_dict
    # check memory empty when update embd_id, memory_type
    memory_size = get_memory_size_cache(memory_id, current_memory.tenant_id)
    not_allowed_update = [f for f in ["tenant_embd_id", "embd_id", "memory_type"] if f in to_update and memory_size > 0]
    if not_allowed_update:
        raise ArgumentException(f"Can't update {not_allowed_update} when memory isn't empty.")
    if "memory_type" in to_update:
        if "system_prompt" not in to_update and judge_system_prompt_is_default(current_memory.system_prompt, current_memory.memory_type):
            # update old default prompt, assemble a new one
            to_update["system_prompt"] = PromptAssembler.assemble_system_prompt({"memory_type": to_update["memory_type"]})

    MemoryService.update_memory(current_memory.tenant_id, memory_id, to_update)
    updated_memory = MemoryService.get_by_memory_id(memory_id)
    return True, format_ret_data_from_memory(updated_memory)