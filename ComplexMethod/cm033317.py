async def _retrieval():
        local_doc_ids = list(doc_ids) if doc_ids else []
        tenant_ids = []

        meta_data_filter = {}
        chat_mdl = None
        if req.get("search_id", ""):
            search_config = SearchService.get_detail(req.get("search_id", "")).get("search_config", {})
            meta_data_filter = search_config.get("meta_data_filter", {})
            if meta_data_filter.get("method") in ["auto", "semi_auto"]:
                chat_id = search_config.get("chat_id", "")
                if chat_id:
                    chat_model_config = get_model_config_by_type_and_name(user_id, LLMType.CHAT, search_config["chat_id"])
                else:
                    chat_model_config = get_tenant_default_model_by_type(user_id, LLMType.CHAT)
                chat_mdl = LLMBundle(user_id, chat_model_config)
        else:
            meta_data_filter = req.get("meta_data_filter") or {}
            if meta_data_filter.get("method") in ["auto", "semi_auto"]:
                chat_model_config = get_tenant_default_model_by_type(user_id, LLMType.CHAT)
                chat_mdl = LLMBundle(user_id, chat_model_config)

        if meta_data_filter:
            metas = DocMetadataService.get_flatted_meta_by_kbs(kb_ids)
            local_doc_ids = await apply_meta_data_filter(meta_data_filter, metas, question, chat_mdl, local_doc_ids)

        tenants = UserTenantService.query(user_id=user_id)
        for kb_id in kb_ids:
            for tenant in tenants:
                if KnowledgebaseService.query(
                        tenant_id=tenant.tenant_id, id=kb_id):
                    tenant_ids.append(tenant.tenant_id)
                    break
            else:
                return get_json_result(
                    data=False, message='Only owner of dataset authorized for this operation.',
                    code=RetCode.OPERATING_ERROR)

        e, kb = KnowledgebaseService.get_by_id(kb_ids[0])
        if not e:
            return get_data_error_result(message="Knowledgebase not found!")

        _question = question
        if langs:
            _question = await cross_languages(kb.tenant_id, None, _question, langs)
        if kb.tenant_embd_id:
            embd_model_config = get_model_config_by_id(kb.tenant_embd_id)
        elif kb.embd_id:
            embd_model_config = get_model_config_by_type_and_name(kb.tenant_id, LLMType.EMBEDDING, kb.embd_id)
        else:
            embd_model_config = get_tenant_default_model_by_type(kb.tenant_id, LLMType.EMBEDDING)
        embd_mdl = LLMBundle(kb.tenant_id, embd_model_config)

        rerank_mdl = None
        if req.get("tenant_rerank_id"):
            rerank_model_config = get_model_config_by_id(req["tenant_rerank_id"])
            rerank_mdl = LLMBundle(kb.tenant_id, rerank_model_config)
        elif req.get("rerank_id"):
            rerank_model_config = get_model_config_by_type_and_name(kb.tenant_id, LLMType.RERANK.value, req["rerank_id"])
            rerank_mdl = LLMBundle(kb.tenant_id, rerank_model_config)

        if req.get("keyword", False):
            default_chat_model_config = get_tenant_default_model_by_type(kb.tenant_id, LLMType.CHAT)
            chat_mdl = LLMBundle(kb.tenant_id, default_chat_model_config)
            _question += await keyword_extraction(chat_mdl, _question)

        labels = label_question(_question, [kb])
        ranks = await settings.retriever.retrieval(
                        _question,
                        embd_mdl,
                        tenant_ids,
                        kb_ids,
                        page,
                        size,
                        float(req.get("similarity_threshold", 0.0)),
                        float(req.get("vector_similarity_weight", 0.3)),
                        doc_ids=local_doc_ids,
                        top=top,
                        rerank_mdl=rerank_mdl,
                        rank_feature=labels
                    )

        if use_kg:
            default_chat_model_config = get_tenant_default_model_by_type(user_id, LLMType.CHAT)
            ck = await settings.kg_retriever.retrieval(_question,
                                                   tenant_ids,
                                                   kb_ids,
                                                   embd_mdl,
                                                   LLMBundle(kb.tenant_id, default_chat_model_config))
            if ck["content_with_weight"]:
                ranks["chunks"].insert(0, ck)
        ranks["chunks"] = settings.retriever.retrieval_by_children(ranks["chunks"], tenant_ids)

        for c in ranks["chunks"]:
            c.pop("vector", None)
        ranks["labels"] = labels

        return get_json_result(data=ranks)