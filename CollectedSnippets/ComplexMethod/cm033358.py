async def retrieval_test(tenant_id):
    """
    Retrieve chunks based on a query.
    ---
    tags:
      - Retrieval
    security:
      - ApiKeyAuth: []
    parameters:
      - in: body
        name: body
        description: Retrieval parameters.
        required: true
        schema:
          type: object
          properties:
            dataset_ids:
              type: array
              items:
                type: string
              required: true
              description: List of dataset IDs to search in.
            question:
              type: string
              required: true
              description: Query string.
            document_ids:
              type: array
              items:
                type: string
              description: List of document IDs to filter.
            similarity_threshold:
              type: number
              format: float
              description: Similarity threshold.
            vector_similarity_weight:
              type: number
              format: float
              description: Vector similarity weight.
            top_k:
              type: integer
              description: Maximum number of chunks to return.
            highlight:
              type: boolean
              description: Whether to highlight matched content.
            metadata_condition:
              type: object
              description: metadata filter condition.
      - in: header
        name: Authorization
        type: string
        required: true
        description: Bearer token for authentication.
    responses:
      200:
        description: Retrieval results.
        schema:
          type: object
          properties:
            chunks:
              type: array
              items:
                type: object
                properties:
                  id:
                    type: string
                    description: Chunk ID.
                  content:
                    type: string
                    description: Chunk content.
                  document_id:
                    type: string
                    description: ID of the document.
                  dataset_id:
                    type: string
                    description: ID of the dataset.
                  similarity:
                    type: number
                    format: float
                    description: Similarity score.
    """
    req = await get_request_json()
    if not req.get("dataset_ids"):
        return get_error_data_result("`dataset_ids` is required.")
    kb_ids = req["dataset_ids"]
    if not isinstance(kb_ids, list):
        return get_error_data_result("`dataset_ids` should be a list")
    for id in kb_ids:
        if not KnowledgebaseService.accessible(kb_id=id, user_id=tenant_id):
            return get_error_data_result(f"You don't own the dataset {id}.")
    kbs = KnowledgebaseService.get_by_ids(kb_ids)
    embd_nms = list(set([TenantLLMService.split_model_name_and_factory(kb.embd_id)[0] for kb in kbs]))  # remove vendor suffix for comparison
    if len(embd_nms) != 1:
        return get_result(
            message='Datasets use different embedding models."',
            code=RetCode.DATA_ERROR,
        )
    if "question" not in req:
        return get_error_data_result("`question` is required.")
    page = int(req.get("page", 1))
    size = int(req.get("page_size", 30))
    question = req["question"]
    # Trim whitespace and validate question
    if isinstance(question, str):
        question = question.strip()
    # Return empty result if question is empty or whitespace-only
    if not question:
        return get_result(data={"total": 0, "chunks": [], "doc_aggs": {}})
    doc_ids = req.get("document_ids", [])
    use_kg = req.get("use_kg", False)
    toc_enhance = req.get("toc_enhance", False)
    langs = req.get("cross_languages", [])
    if not isinstance(doc_ids, list):
        return get_error_data_result("`documents` should be a list")
    if doc_ids:
        doc_ids_list = KnowledgebaseService.list_documents_by_ids(kb_ids)
        for doc_id in doc_ids:
            if doc_id not in doc_ids_list:
                return get_error_data_result(f"The datasets don't own the document {doc_id}")
    if not doc_ids:
        metadata_condition = req.get("metadata_condition")
        if metadata_condition:
            metas = DocMetadataService.get_flatted_meta_by_kbs(kb_ids)
            doc_ids = meta_filter(metas, convert_conditions(metadata_condition), metadata_condition.get("logic", "and"))
            # If metadata_condition has conditions but no docs match, return empty result
            if not doc_ids and metadata_condition.get("conditions"):
                return get_result(data={"total": 0, "chunks": [], "doc_aggs": {}})
            if metadata_condition and not doc_ids:
                doc_ids = ["-999"]
        else:
            # If doc_ids is None all documents of the datasets are used
            doc_ids = None
    similarity_threshold = float(req.get("similarity_threshold", 0.2))
    vector_similarity_weight = float(req.get("vector_similarity_weight", 0.3))
    top = int(req.get("top_k", 1024))
    highlight_val = req.get("highlight", None)
    if highlight_val is None:
        highlight = False
    elif isinstance(highlight_val, bool):
        highlight = highlight_val
    elif isinstance(highlight_val, str):
        if highlight_val.lower() in ["true", "false"]:
            highlight = highlight_val.lower() == "true"
        else:
            return get_error_data_result("`highlight` should be a boolean")
    else:
        return get_error_data_result("`highlight` should be a boolean")
    try:
        tenant_ids = list(set([kb.tenant_id for kb in kbs]))
        e, kb = KnowledgebaseService.get_by_id(kb_ids[0])
        if not e:
            return get_error_data_result(message="Dataset not found!")
        if kb.tenant_embd_id:
            embd_model_config = get_model_config_by_id(kb.tenant_embd_id)
        else:
            embd_model_config = get_model_config_by_type_and_name(kb.tenant_id, LLMType.EMBEDDING, kb.embd_id)
        embd_mdl = LLMBundle(kb.tenant_id, embd_model_config)

        rerank_mdl = None
        if req.get("tenant_rerank_id"):
            rerank_model_config = get_model_config_by_id(req["tenant_rerank_id"])
            rerank_mdl = LLMBundle(kb.tenant_id, rerank_model_config)
        elif req.get("rerank_id"):
            rerank_model_config = get_model_config_by_type_and_name(kb.tenant_id, LLMType.RERANK, req["rerank_id"])
            rerank_mdl = LLMBundle(kb.tenant_id, rerank_model_config)

        if langs:
            question = await cross_languages(kb.tenant_id, None, question, langs)

        if req.get("keyword", False):
            chat_model_config = get_tenant_default_model_by_type(kb.tenant_id, LLMType.CHAT)
            chat_mdl = LLMBundle(kb.tenant_id, chat_model_config)
            question += await keyword_extraction(chat_mdl, question)

        ranks = await settings.retriever.retrieval(
            question,
            embd_mdl,
            tenant_ids,
            kb_ids,
            page,
            size,
            similarity_threshold,
            vector_similarity_weight,
            top,
            doc_ids,
            rerank_mdl=rerank_mdl,
            highlight=highlight,
            rank_feature=label_question(question, kbs),
        )
        if toc_enhance:
            chat_model_config = get_tenant_default_model_by_type(kb.tenant_id, LLMType.CHAT)
            chat_mdl = LLMBundle(kb.tenant_id, chat_model_config)
            cks = await settings.retriever.retrieval_by_toc(question, ranks["chunks"], tenant_ids, chat_mdl, size)
            if cks:
                ranks["chunks"] = cks
        ranks["chunks"] = settings.retriever.retrieval_by_children(ranks["chunks"], tenant_ids)
        if use_kg:
            chat_model_config = get_tenant_default_model_by_type(kb.tenant_id, LLMType.CHAT)
            ck = await settings.kg_retriever.retrieval(question, [k.tenant_id for k in kbs], kb_ids, embd_mdl, LLMBundle(kb.tenant_id, chat_model_config))
            if ck["content_with_weight"]:
                ranks["chunks"].insert(0, ck)

        for c in ranks["chunks"]:
            c.pop("vector", None)

        ##rename keys
        renamed_chunks = []
        for chunk in ranks["chunks"]:
            key_mapping = {
                "chunk_id": "id",
                "content_with_weight": "content",
                "doc_id": "document_id",
                "important_kwd": "important_keywords",
                "question_kwd": "questions",
                "docnm_kwd": "document_keyword",
                "kb_id": "dataset_id",
            }
            rename_chunk = {}
            for key, value in chunk.items():
                new_key = key_mapping.get(key, key)
                rename_chunk[new_key] = value
            renamed_chunks.append(rename_chunk)
        ranks["chunks"] = renamed_chunks
        return get_result(data=ranks)
    except Exception as e:
        if str(e).find("not_found") > 0:
            return get_result(
                message="No chunk found! Check the chunk status please!",
                code=RetCode.DATA_ERROR,
            )
        return server_error_response(e)