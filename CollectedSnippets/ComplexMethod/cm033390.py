async def get_memory_messages(memory_id, agent_ids: list[str], keywords: str, page: int=1, page_size: int = 50):
    memory = MemoryService.get_by_memory_id(memory_id)
    if not memory:
        raise NotFoundException(f"Memory '{memory_id}' not found.")
    messages = MessageService.list_message(
        memory.tenant_id, memory_id, agent_ids, keywords, page, page_size)
    agent_name_mapping = {}
    extract_task_mapping = {}
    if messages["message_list"]:
        agent_list = UserCanvasService.get_basic_info_by_canvas_ids([message["agent_id"] for message in messages["message_list"]])
        agent_name_mapping = {agent["id"]: agent["title"] for agent in agent_list}
        task_list = TaskService.get_tasks_progress_by_doc_ids([memory_id])
        if task_list:
            task_list.sort(key=lambda t: t["create_time"]) # asc, use newer when exist more than one task
            for task in task_list:
                # the 'digest' field carries the source_id when a task is created, so use 'digest' as key
                extract_task_mapping.update({int(task["digest"]): task})
    for message in messages["message_list"]:
        message["agent_name"] = agent_name_mapping.get(message["agent_id"], "Unknown")
        message["task"] = extract_task_mapping.get(message["message_id"], {})
        for extract_msg in message["extract"]:
            extract_msg["agent_name"] = agent_name_mapping.get(extract_msg["agent_id"], "Unknown")
    return {"messages": messages, "storage_type": memory.storage_type}