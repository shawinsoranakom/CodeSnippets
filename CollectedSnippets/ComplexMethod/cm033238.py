async def async_chat_solo(dialog, messages, stream=True):
    llm_type = TenantLLMService.llm_id2llm_type(dialog.llm_id)
    attachments = ""
    image_attachments = []
    image_files = []
    if "files" in messages[-1]:
        if llm_type == "chat":
            text_attachments, image_attachments = split_file_attachments(messages[-1]["files"])
        else:
            text_attachments, image_files = split_file_attachments(messages[-1]["files"], raw=True)
        attachments = "\n\n".join(text_attachments)

    if dialog.llm_id:
        model_config = get_model_config_by_type_and_name(dialog.tenant_id, LLMType.CHAT, dialog.llm_id)
    elif dialog.tenant_llm_id:
        model_config = get_model_config_by_id(dialog.tenant_llm_id)
    else:
        model_config = get_tenant_default_model_by_type(dialog.tenant_id, LLMType.CHAT)

    chat_mdl = LLMBundle(dialog.tenant_id, model_config)
    factory = model_config.get("llm_factory", "") if model_config else ""

    prompt_config = dialog.prompt_config
    tts_mdl = None
    if prompt_config.get("tts"):
        default_tts_model = get_tenant_default_model_by_type(dialog.tenant_id, LLMType.TTS)
        tts_mdl = LLMBundle(dialog.tenant_id, default_tts_model)
    msg = [{"role": m["role"], "content": re.sub(r"##\d+\$\$", "", m["content"])} for m in messages if m["role"] != "system"]
    if attachments and msg:
        msg[-1]["content"] += attachments
    if llm_type == "chat" and image_attachments:
        convert_last_user_msg_to_multimodal(msg, image_attachments, factory)
    if stream:
        if llm_type == "chat":
            stream_iter = chat_mdl.async_chat_streamly_delta(prompt_config.get("system", ""), msg, dialog.llm_setting)
        else:
            stream_iter = chat_mdl.async_chat_streamly_delta(prompt_config.get("system", ""), msg, dialog.llm_setting, images=image_files)
        async for kind, value, state in _stream_with_think_delta(stream_iter):
            if kind == "marker":
                flags = {"start_to_think": True} if value == "<think>" else {"end_to_think": True}
                yield {"answer": "", "reference": {}, "audio_binary": None, "prompt": "", "created_at": time.time(), "final": False, **flags}
                continue
            yield {"answer": value, "reference": {}, "audio_binary": tts(tts_mdl, value), "prompt": "", "created_at": time.time(), "final": False}
    else:
        if llm_type == "chat":
            answer = await chat_mdl.async_chat(prompt_config.get("system", ""), msg, dialog.llm_setting)
        else:
            answer = await chat_mdl.async_chat(prompt_config.get("system", ""), msg, dialog.llm_setting, images=image_files)
        user_content = msg[-1].get("content", "[content not available]")
        logging.debug("User: {}|Assistant: {}".format(user_content, answer))
        yield {"answer": answer, "reference": {}, "audio_binary": tts(tts_mdl, answer), "prompt": "", "created_at": time.time()}