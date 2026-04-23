async def update_chunk(tenant_id, dataset_id, document_id, chunk_id):
    """
    Update a chunk within a document.
    ---
    tags:
      - Chunks
    security:
      - ApiKeyAuth: []
    parameters:
      - in: path
        name: dataset_id
        type: string
        required: true
        description: ID of the dataset.
      - in: path
        name: document_id
        type: string
        required: true
        description: ID of the document.
      - in: path
        name: chunk_id
        type: string
        required: true
        description: ID of the chunk to update.
      - in: body
        name: body
        description: Chunk update parameters.
        required: true
        schema:
          type: object
          properties:
            content:
              type: string
              description: Updated content of the chunk.
            important_keywords:
              type: array
              items:
                type: string
              description: Updated important keywords.
            tag_kwd:
              type: array
              items:
                type: string
              description: Updated tag keywords.
            available:
              type: boolean
              description: Availability status of the chunk.
      - in: header
        name: Authorization
        type: string
        required: true
        description: Bearer token for authentication.
    responses:
      200:
        description: Chunk updated successfully.
        schema:
          type: object
    """
    chunk = settings.docStoreConn.get(chunk_id, search.index_name(tenant_id), [dataset_id])
    if chunk is None:
        return get_error_data_result(f"Can't find this chunk {chunk_id}")
    if not KnowledgebaseService.accessible(kb_id=dataset_id, user_id=tenant_id):
        return get_error_data_result(message=f"You don't own the dataset {dataset_id}.")
    doc = DocumentService.query(id=document_id, kb_id=dataset_id)
    if not doc:
        return get_error_data_result(message=f"You don't own the document {document_id}.")
    doc = doc[0]
    req = await get_request_json()
    content = req.get("content")
    if content is not None:
        if is_content_empty(content):
            return get_error_data_result(message="`content` is required")
    else:
        content = chunk.get("content_with_weight", "")
    d = {"id": chunk_id, "content_with_weight": content}
    d["content_ltks"] = rag_tokenizer.tokenize(d["content_with_weight"])
    d["content_sm_ltks"] = rag_tokenizer.fine_grained_tokenize(d["content_ltks"])
    if "important_keywords" in req:
        if not isinstance(req["important_keywords"], list):
            return get_error_data_result("`important_keywords` should be a list")
        d["important_kwd"] = req.get("important_keywords", [])
        d["important_tks"] = rag_tokenizer.tokenize(" ".join(req["important_keywords"]))
    if "questions" in req:
        if not isinstance(req["questions"], list):
            return get_error_data_result("`questions` should be a list")
        d["question_kwd"] = [str(q).strip() for q in req.get("questions", []) if str(q).strip()]
        d["question_tks"] = rag_tokenizer.tokenize("\n".join(req["questions"]))
    if "available" in req:
        d["available_int"] = int(req["available"])
    if "positions" in req:
        if not isinstance(req["positions"], list):
            return get_error_data_result("`positions` should be a list")
        d["position_int"] = req["positions"]
    if "tag_kwd" in req:
        if not isinstance(req["tag_kwd"], list):
            return get_error_data_result("`tag_kwd` should be a list")
        if not all(isinstance(t, str) for t in req["tag_kwd"]):
            return get_error_data_result("`tag_kwd` must be a list of strings")
        d["tag_kwd"] = req["tag_kwd"]
    if "tag_feas" in req:
        try:
            d["tag_feas"] = validate_tag_features(req["tag_feas"])
        except ValueError as exc:
            return get_error_data_result(f"`tag_feas` {exc}")
    tenant_embd_id = DocumentService.get_tenant_embd_id(document_id)
    if tenant_embd_id:
        model_config = get_model_config_by_id(tenant_embd_id)
    else:
        embd_id = DocumentService.get_embd_id(document_id)
        model_config = get_model_config_by_type_and_name(tenant_id, LLMType.EMBEDDING.value, embd_id)
    embd_mdl = TenantLLMService.model_instance(model_config)
    if doc.parser_id == ParserType.QA:
        arr = [t for t in re.split(r"[\n\t]", d["content_with_weight"]) if len(t) > 1]
        if len(arr) != 2:
            return get_error_data_result(message="Q&A must be separated by TAB/ENTER key.")
        q, a = rmPrefix(arr[0]), rmPrefix(arr[1])
        d = beAdoc(d, arr[0], arr[1], not any([rag_tokenizer.is_chinese(t) for t in q + a]))

    v, c = embd_mdl.encode([doc.name, d["content_with_weight"] if not d.get("question_kwd") else "\n".join(d["question_kwd"])])
    v = 0.1 * v[0] + 0.9 * v[1] if doc.parser_id != ParserType.QA else v[1]
    d["q_%d_vec" % len(v)] = v.tolist()
    settings.docStoreConn.update({"id": chunk_id}, d, search.index_name(tenant_id), dataset_id)
    return get_result()