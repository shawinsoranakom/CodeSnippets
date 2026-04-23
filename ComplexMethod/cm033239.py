def get_models(dialog):
    embd_mdl, chat_mdl, rerank_mdl, tts_mdl = None, None, None, None
    kbs = KnowledgebaseService.get_by_ids(dialog.kb_ids)
    embedding_list = list(set([kb.embd_id for kb in kbs]))
    if len(embedding_list) > 1:
        raise Exception("**ERROR**: Knowledge bases use different embedding models.")

    if embedding_list:
        embd_owner_tenant_id = kbs[0].tenant_id
        embd_model_config = get_model_config_by_type_and_name(embd_owner_tenant_id, LLMType.EMBEDDING, embedding_list[0])
        embd_mdl = LLMBundle(embd_owner_tenant_id, embd_model_config)
        if not embd_mdl:
            raise LookupError("Embedding model(%s) not found" % embedding_list[0])

    if dialog.llm_id:
        chat_model_config = get_model_config_by_type_and_name(dialog.tenant_id, LLMType.CHAT, dialog.llm_id)
    elif dialog.tenant_llm_id:
        chat_model_config = get_model_config_by_id(dialog.tenant_llm_id)
    else:
        chat_model_config = get_tenant_default_model_by_type(dialog.tenant_id, LLMType.CHAT)

    chat_mdl = LLMBundle(dialog.tenant_id, chat_model_config)

    if dialog.rerank_id:
        rerank_model_config = get_model_config_by_type_and_name(dialog.tenant_id, LLMType.RERANK, dialog.rerank_id)
        rerank_mdl = LLMBundle(dialog.tenant_id, rerank_model_config)

    if dialog.prompt_config.get("tts"):
        default_tts_model_config = get_tenant_default_model_by_type(dialog.tenant_id, LLMType.TTS)
        tts_mdl = LLMBundle(dialog.tenant_id, default_tts_model_config)
    return kbs, embd_mdl, rerank_mdl, chat_mdl, tts_mdl