async def embed_and_save(memory, message_list: list[dict], task_id: str=None):
    if memory.tenant_embd_id:
        embd_model_config = get_model_config_by_id(memory.tenant_embd_id)
    else:
        embd_model_config = get_model_config_by_type_and_name(memory.tenant_id, LLMType.EMBEDDING, memory.embd_id)
    embedding_model = LLMBundle(memory.tenant_id, embd_model_config)
    if task_id:
        TaskService.update_progress(task_id, {"progress": 0.65, "progress_msg": timestamp_to_date(current_timestamp())+ " " + "Prepared embedding model."})
    vector_list, _ = embedding_model.encode([msg["content"] for msg in message_list])
    for idx, msg in enumerate(message_list):
        msg["content_embed"] = vector_list[idx]
    if task_id:
        TaskService.update_progress(task_id, {"progress": 0.85, "progress_msg": timestamp_to_date(current_timestamp())+ " " + "Embedded extracted content."})
    vector_dimension = len(vector_list[0])
    if not MessageService.has_index(memory.tenant_id, memory.id):
        created = MessageService.create_index(memory.tenant_id, memory.id, vector_size=vector_dimension)
        if not created:
            error_msg = "Failed to create message index."
            if task_id:
                TaskService.update_progress(task_id, {"progress": -1, "progress_msg": timestamp_to_date(current_timestamp())+ " " + error_msg})
            return False, error_msg

    new_msg_size = sum([MessageService.calculate_message_size(m) for m in message_list])
    current_memory_size = get_memory_size_cache(memory.tenant_id, memory.id)
    if new_msg_size + current_memory_size > memory.memory_size:
        size_to_delete = current_memory_size + new_msg_size - memory.memory_size
        if memory.forgetting_policy == "FIFO":
            message_ids_to_delete, delete_size = MessageService.pick_messages_to_delete_by_fifo(memory.id, memory.tenant_id,
                                                                                                size_to_delete)
            MessageService.delete_message({"message_id": message_ids_to_delete}, memory.tenant_id, memory.id)
            decrease_memory_size_cache(memory.id, delete_size)
        else:
            error_msg = "Failed to insert message into memory. Memory size reached limit and cannot decide which to delete."
            if task_id:
                TaskService.update_progress(task_id, {"progress": -1, "progress_msg": timestamp_to_date(current_timestamp())+ " " + error_msg})
            return False, error_msg
    fail_cases = MessageService.insert_message(message_list, memory.tenant_id, memory.id)
    if fail_cases:
        error_msg = "Failed to insert message into memory. Details: " + "; ".join(fail_cases)
        if task_id:
            TaskService.update_progress(task_id, {"progress": -1, "progress_msg": timestamp_to_date(current_timestamp())+ " " + error_msg})
        return False, error_msg

    if task_id:
        TaskService.update_progress(task_id, {"progress": 0.95, "progress_msg": timestamp_to_date(current_timestamp())+ " " + "Saved messages to storage."})
    increase_memory_size_cache(memory.id, new_msg_size)
    return True, "Message saved successfully."