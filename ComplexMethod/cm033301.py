async def queue_save_to_memory_task(memory_ids: list[str], message_dict: dict):
    """
    :param memory_ids:
    :param message_dict: {
        "user_id": str,
        "agent_id": str,
        "session_id": str,
        "user_input": str,
        "agent_response": str
    }
    """
    def new_task(_memory_id: str, _source_id: int):
        return {
            "id": get_uuid(),
            "doc_id": _memory_id,
            "task_type": "memory",
            "progress": 0.0,
            "digest": str(_source_id)
        }

    not_found_memory = []
    failed_memory = []
    for memory_id in memory_ids:
        memory = MemoryService.get_by_memory_id(memory_id)
        if not memory:
            not_found_memory.append(memory_id)
            continue

        raw_message_id = REDIS_CONN.generate_auto_increment_id(namespace="memory")
        raw_message = {
            "message_id": raw_message_id,
            "message_type": MemoryType.RAW.name.lower(),
            "source_id": 0,
            "memory_id": memory_id,
            "user_id": message_dict.get("user_id", ""),
            "agent_id": message_dict["agent_id"],
            "session_id": message_dict["session_id"],
            "content": f"User Input: {message_dict.get('user_input')}\nAgent Response: {message_dict.get('agent_response')}",
            "valid_at": timestamp_to_date(current_timestamp()),
            "invalid_at": None,
            "forget_at": None,
            "status": True
        }
        res, msg = await embed_and_save(memory, [raw_message])
        if not res:
            failed_memory.append({"memory_id": memory_id, "fail_msg": msg})
            continue

        task = new_task(memory_id, raw_message_id)
        bulk_insert_into_db(Task, [task], replace_on_conflict=True)
        task_message = {
            "id": task["id"],
            "task_id": task["id"],
            "task_type": task["task_type"],
            "memory_id": memory_id,
            "source_id": raw_message_id,
            "message_dict": message_dict
        }
        if not REDIS_CONN.queue_product(settings.get_svr_queue_name(priority=0), message=task_message):
            failed_memory.append({"memory_id": memory_id, "fail_msg": "Can't access Redis."})

    error_msg = ""
    if not_found_memory:
        error_msg = f"Memory {not_found_memory} not found."
    if failed_memory:
        error_msg += "".join([f"Memory {fm['memory_id']} failed. Detail: {fm['fail_msg']}" for fm in failed_memory])

    if error_msg:
        return False, error_msg

    return True, "All add to task."