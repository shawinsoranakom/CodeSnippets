async def add_chunk(tenant_id, dataset_id, document_id):
    """
    Add a chunk to a document.
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
      - in: body
        name: body
        description: Chunk data.
        required: true
        schema:
          type: object
          properties:
            content:
              type: string
              required: true
              description: Content of the chunk.
            important_keywords:
              type: array
              items:
                type: string
              description: Important keywords.
            image_base64:
              type: string
              description: Base64-encoded image to associate with the chunk.
      - in: header
        name: Authorization
        type: string
        required: true
        description: Bearer token for authentication.
    responses:
      200:
        description: Chunk added successfully.
        schema:
          type: object
          properties:
            chunk:
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
                important_keywords:
                  type: array
                  items:
                    type: string
                  description: Important keywords.
    """
    if not KnowledgebaseService.accessible(kb_id=dataset_id, user_id=tenant_id):
        return get_error_data_result(message=f"You don't own the dataset {dataset_id}.")
    doc = DocumentService.query(id=document_id, kb_id=dataset_id)
    if not doc:
        return get_error_data_result(message=f"You don't own the document {document_id}.")
    doc = doc[0]
    req = await get_request_json()
    if is_content_empty(req.get("content")):
        return get_error_data_result(message="`content` is required")
    if "important_keywords" in req:
        if not isinstance(req["important_keywords"], list):
            return get_error_data_result("`important_keywords` is required to be a list")
    if "questions" in req:
        if not isinstance(req["questions"], list):
            return get_error_data_result("`questions` is required to be a list")
    chunk_id = xxhash.xxh64((req["content"] + document_id).encode("utf-8")).hexdigest()
    d = {
        "id": chunk_id,
        "content_ltks": rag_tokenizer.tokenize(req["content"]),
        "content_with_weight": req["content"],
    }
    d["content_sm_ltks"] = rag_tokenizer.fine_grained_tokenize(d["content_ltks"])
    d["important_kwd"] = req.get("important_keywords", [])
    d["important_tks"] = rag_tokenizer.tokenize(" ".join(req.get("important_keywords", [])))
    d["question_kwd"] = [str(q).strip() for q in req.get("questions", []) if str(q).strip()]
    d["question_tks"] = rag_tokenizer.tokenize("\n".join(req.get("questions", [])))
    d["create_time"] = str(datetime.datetime.now()).replace("T", " ")[:19]
    d["create_timestamp_flt"] = datetime.datetime.now().timestamp()
    d["kb_id"] = dataset_id
    d["docnm_kwd"] = doc.name
    d["doc_id"] = document_id
    if "tag_kwd" in req:
        if not isinstance(req["tag_kwd"], list):
            return get_error_data_result("`tag_kwd` is required to be a list")
        if not all(isinstance(t, str) for t in req["tag_kwd"]):
            return get_error_data_result("`tag_kwd` must be a list of strings")
        d["tag_kwd"] = req["tag_kwd"]
    if "tag_feas" in req:
        try:
            d["tag_feas"] = validate_tag_features(req["tag_feas"])
        except ValueError as exc:
            return get_error_data_result(f"`tag_feas` {exc}")
    import base64

    image_base64 = req.get("image_base64", None)
    if image_base64:
        d["img_id"] = "{}-{}".format(dataset_id, chunk_id)
        d["doc_type_kwd"] = "image"

    tenant_embd_id = DocumentService.get_tenant_embd_id(document_id)
    if tenant_embd_id:
        model_config = get_model_config_by_id(tenant_embd_id)
    else:
        embd_id = DocumentService.get_embd_id(document_id)
        model_config = get_model_config_by_type_and_name(tenant_id, LLMType.EMBEDDING.value, embd_id)
    embd_mdl = TenantLLMService.model_instance(model_config)
    v, c = embd_mdl.encode([doc.name, req["content"] if not d["question_kwd"] else "\n".join(d["question_kwd"])])
    v = 0.1 * v[0] + 0.9 * v[1]
    d["q_%d_vec" % len(v)] = v.tolist()
    settings.docStoreConn.insert([d], search.index_name(tenant_id), dataset_id)

    if image_base64:
        store_chunk_image(dataset_id, chunk_id, base64.b64decode(image_base64))

    DocumentService.increment_chunk_num(doc.id, doc.kb_id, c, 1, 0)
    # rename keys
    key_mapping = {
        "id": "id",
        "content_with_weight": "content",
        "doc_id": "document_id",
        "important_kwd": "important_keywords",
        "tag_kwd": "tag_kwd",
        "question_kwd": "questions",
        "kb_id": "dataset_id",
        "create_timestamp_flt": "create_timestamp",
        "create_time": "create_time",
        "document_keyword": "document",
        "img_id": "image_id",
    }
    renamed_chunk = {}
    for key, value in d.items():
        if key in key_mapping:
            new_key = key_mapping.get(key, key)
            renamed_chunk[new_key] = value
    _ = Chunk(**renamed_chunk)  # validate the chunk
    return get_result(data={"chunk": renamed_chunk})