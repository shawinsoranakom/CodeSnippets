async def extract_by_llm(tenant_id: str, tenant_llm_id: int, extract_conf: dict, memory_type: List[str], user_input: str,
                         agent_response: str, system_prompt: str = "", user_prompt: str="", task_id: str=None, llm_id: str = "") -> List[dict]:
    if not system_prompt:
        system_prompt = PromptAssembler.assemble_system_prompt({"memory_type": memory_type})
    conversation_content = f"User Input: {user_input}\nAgent Response: {agent_response}"
    conversation_time = timestamp_to_date(current_timestamp())
    user_prompts = []
    if user_prompt:
        user_prompts.append({"role": "user", "content": user_prompt})
        user_prompts.append({"role": "user", "content": f"Conversation: {conversation_content}\nConversation Time: {conversation_time}\nCurrent Time: {conversation_time}"})
    else:
        user_prompts.append({"role": "user", "content": PromptAssembler.assemble_user_prompt(conversation_content, conversation_time, conversation_time)})
    if tenant_llm_id:
        llm_config = get_model_config_by_id(tenant_llm_id)
    else:
        llm_config = get_model_config_by_type_and_name(tenant_id, LLMType.CHAT, llm_id)
    llm = LLMBundle(tenant_id, llm_config)
    if task_id:
        TaskService.update_progress(task_id, {"progress": 0.15, "progress_msg": timestamp_to_date(current_timestamp())+ " " + "Prepared prompts and LLM."})
    res = await llm.async_chat(system_prompt, user_prompts, extract_conf)
    res_json = get_json_result_from_llm_response(res)
    if task_id:
        TaskService.update_progress(task_id, {"progress": 0.35, "progress_msg": timestamp_to_date(current_timestamp())+ " " + "Get extracted result from LLM."})
    return [{
        "content": extracted_content["content"],
        "valid_at": format_iso_8601_to_ymd_hms(extracted_content["valid_at"]),
        "invalid_at": format_iso_8601_to_ymd_hms(extracted_content["invalid_at"]) if extracted_content.get("invalid_at") else "",
        "message_type": message_type
    } for message_type, extracted_content_list in res_json.items() for extracted_content in extracted_content_list]