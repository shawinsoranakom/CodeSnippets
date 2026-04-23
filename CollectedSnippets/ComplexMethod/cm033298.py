async def save_extracted_to_memory_only(memory_id: str, message_dict, source_message_id: int, task_id: str=None):
    memory = MemoryService.get_by_memory_id(memory_id)
    if not memory:
        msg = f"Memory '{memory_id}' not found."
        if task_id:
            TaskService.update_progress(task_id, {"progress": -1, "progress_msg": timestamp_to_date(current_timestamp())+ " " + msg})
        return False, msg

    if memory.memory_type == MemoryType.RAW.value:
        msg = f"Memory '{memory_id}' don't need to extract."
        if task_id:
            TaskService.update_progress(task_id, {"progress": 1.0, "progress_msg": timestamp_to_date(current_timestamp())+ " " + msg})
        return True, msg

    tenant_id = memory.tenant_id
    extracted_content = await extract_by_llm(
        tenant_id,
        memory.tenant_llm_id,
        {"temperature": memory.temperature},
        get_memory_type_human(memory.memory_type),
        message_dict.get("user_input", ""),
        message_dict.get("agent_response", ""),
        task_id=task_id,
        llm_id=memory.llm_id
    )
    message_list = [{
        "message_id": REDIS_CONN.generate_auto_increment_id(namespace="memory"),
        "message_type": content["message_type"],
        "source_id": source_message_id,
        "memory_id": memory_id,
        "user_id": message_dict.get("user_id", ""),
        "agent_id": message_dict["agent_id"],
        "session_id": message_dict["session_id"],
        "content": content["content"],
        "valid_at": content["valid_at"],
        "invalid_at": content["invalid_at"] if content["invalid_at"] else None,
        "forget_at": None,
        "status": True
    } for content in extracted_content]
    if not message_list:
        msg = "No memory extracted from raw message."
        if task_id:
            TaskService.update_progress(task_id, {"progress": 1.0, "progress_msg": timestamp_to_date(current_timestamp())+ " " + msg})
        return True, msg

    if task_id:
        TaskService.update_progress(task_id, {"progress": 0.5, "progress_msg": timestamp_to_date(current_timestamp())+ " " + f"Extracted {len(message_list)} messages from raw dialogue."})
    return await embed_and_save(memory, message_list, task_id)