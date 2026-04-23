async def _retrieval():
        nonlocal similarity_threshold, vector_similarity_weight, top, rerank_id
        local_doc_ids = list(doc_ids) if doc_ids else []
        tenant_ids = []
        _question = question

        meta_data_filter = {}
        chat_mdl = None
        if req.get("search_id", ""):
            search_config = SearchService.get_detail(req.get("search_id", "")).get("search_config", {})
            meta_data_filter = search_config.get("meta_data_filter", {})
            if meta_data_filter.get("method") in ["auto", "semi_auto"]:
                chat_id = search_config.get("chat_id", "")
                if chat_id:
                    chat_model_config = get_model_config_by_type_and_name(tenant_id, LLMType.CHAT, chat_id)
                else:
                    chat_model_config = get_tenant_default_model_by_type(tenant_id, LLMType.CHAT)
                chat_mdl = LLMBundle(tenant_id, chat_model_config)
            # Apply search_config settings if not explicitly provided in request
            if not req.get("similarity_threshold"):
                similarity_threshold = float(search_config.get("similarity_threshold", similarity_threshold))
            if not req.get("vector_similarity_weight"):
                vector_similarity_weight = float(search_config.get("vector_similarity_weight", vector_similarity_weight))
            if not req.get("top_k"):
                top = int(search_config.get("top_k", top))
            if not req.get("rerank_id"):
                rerank_id = search_config.get("rerank_id", "")
        else:
            meta_data_filter = req.get("meta_data_filter") or {}
            if meta_data_filter.get("method") in ["auto", "semi_auto"]:
                chat_model_config = get_tenant_default_model_by_type(tenant_id, LLMType.CHAT)
                chat_mdl = LLMBundle(tenant_id, chat_model_config)

        if meta_data_filter:
            metas = DocMetadataService.get_flatted_meta_by_kbs(kb_ids)
            local_doc_ids = await apply_meta_data_filter(meta_data_filter, metas, _question, chat_mdl, local_doc_ids)

        tenants = UserTenantService.query(user_id=tenant_id)
        for kb_id in kb_ids:
            for tenant in tenants:
                if KnowledgebaseService.query(tenant_id=tenant.tenant_id, id=kb_id):
                    tenant_ids.append(tenant.tenant_id)
                    break
            else:
                return get_json_result(data=False, message="Only owner of dataset authorized for this operation.",
                                       code=RetCode.OPERATING_ERROR)

        e, kb = KnowledgebaseService.get_by_id(kb_ids[0])
        if not e:
            return get_error_data_result(message="Knowledgebase not found!")

        if langs:
            _question = await cross_languages(kb.tenant_id, None, _question, langs)
        if kb.tenant_embd_id:
            embd_model_config = get_model_config_by_id(kb.tenant_embd_id)
        else:
            embd_model_config = get_model_config_by_type_and_name(kb.tenant_id, LLMType.EMBEDDING, kb.embd_id)
        embd_mdl = LLMBundle(kb.tenant_id, embd_model_config)

        rerank_mdl = None
        if tenant_rerank_id:
            rerank_model_config = get_model_config_by_id(tenant_rerank_id)
            rerank_mdl = LLMBundle(kb.tenant_id, rerank_model_config)
        elif rerank_id:
            rerank_model_config = get_model_config_by_type_and_name(tenant_id, LLMType.RERANK, rerank_id)
            rerank_mdl = LLMBundle(kb.tenant_id, rerank_model_config)

        if req.get("keyword", False):
            default_chat_model = get_tenant_default_model_by_type(kb.tenant_id, LLMType.CHAT)
            chat_mdl = LLMBundle(kb.tenant_id, default_chat_model)
            _question += await keyword_extraction(chat_mdl, _question)

        labels = label_question(_question, [kb])
        ranks = await settings.retriever.retrieval(
            _question, embd_mdl, tenant_ids, kb_ids, page, size, similarity_threshold, vector_similarity_weight, top,
            local_doc_ids, rerank_mdl=rerank_mdl, highlight=req.get("highlight"), rank_feature=labels
        )
        if use_kg:
            default_chat_model = get_tenant_default_model_by_type(kb.tenant_id, LLMType.CHAT)
            ck = await settings.kg_retriever.retrieval(_question, tenant_ids, kb_ids, embd_mdl,
                                                 LLMBundle(kb.tenant_id, default_chat_model))
            if ck["content_with_weight"]:
                ranks["chunks"].insert(0, ck)

        for c in ranks["chunks"]:
            c.pop("vector", None)
        ranks["labels"] = labels

        return get_json_result(data=ranks)