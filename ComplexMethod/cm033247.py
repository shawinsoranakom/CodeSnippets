async def gen_mindmap(question, kb_ids, tenant_id, search_config={}):
    meta_data_filter = search_config.get("meta_data_filter", {})
    doc_ids = search_config.get("doc_ids", [])
    rerank_id = search_config.get("rerank_id", "")
    rerank_mdl = None
    kbs = KnowledgebaseService.get_by_ids(kb_ids)
    if not kbs:
        return {"error": "No KB selected"}
    tenant_embedding_list = list(set([kb.tenant_embd_id for kb in kbs]))
    tenant_ids = list(set([kb.tenant_id for kb in kbs]))
    if tenant_embedding_list[0]:
        embd_model_config = get_model_config_by_id(tenant_embedding_list[0])
        embd_owner_tenant_id = kbs[0].tenant_id
    else:
        embd_owner_tenant_id = kbs[0].tenant_id
        embd_model_config = get_model_config_by_type_and_name(embd_owner_tenant_id, LLMType.EMBEDDING, kbs[0].embd_id)
    embd_mdl = LLMBundle(embd_owner_tenant_id, embd_model_config)
    chat_id = search_config.get("chat_id", "")
    if chat_id:
        chat_model_config = get_model_config_by_type_and_name(tenant_id, LLMType.CHAT, chat_id)
    else:
        chat_model_config = get_tenant_default_model_by_type(tenant_id, LLMType.CHAT)
    chat_mdl = LLMBundle(tenant_id, chat_model_config)
    if rerank_id:
        rerank_model_config = get_model_config_by_type_and_name(tenant_id, LLMType.RERANK, rerank_id)
        rerank_mdl = LLMBundle(tenant_id, rerank_model_config)

    if meta_data_filter:
        metas = DocMetadataService.get_flatted_meta_by_kbs(kb_ids)
        doc_ids = await apply_meta_data_filter(meta_data_filter, metas, question, chat_mdl, doc_ids)

    ranks = await settings.retriever.retrieval(
        question=question,
        embd_mdl=embd_mdl,
        tenant_ids=tenant_ids,
        kb_ids=kb_ids,
        page=1,
        page_size=12,
        similarity_threshold=search_config.get("similarity_threshold", 0.2),
        vector_similarity_weight=search_config.get("vector_similarity_weight", 0.3),
        top=search_config.get("top_k", 1024),
        doc_ids=doc_ids,
        aggs=False,
        rerank_mdl=rerank_mdl,
        rank_feature=label_question(question, kbs),
    )
    mindmap = MindMapExtractor(chat_mdl)
    mind_map = await mindmap([c["content_with_weight"] for c in ranks["chunks"]])
    return mind_map.output