async def set():
    req = await get_request_json()
    content_with_weight = req["content_with_weight"]
    if not isinstance(content_with_weight, (str, bytes)):
        raise TypeError("expected string or bytes-like object")
    if isinstance(content_with_weight, bytes):
        content_with_weight = content_with_weight.decode("utf-8", errors="ignore")
    if is_content_empty(content_with_weight):
        return get_data_error_result(message="`content_with_weight` is required")
    d = {
        "id": req["chunk_id"],
        "content_with_weight": content_with_weight}
    d["content_ltks"] = rag_tokenizer.tokenize(content_with_weight)
    d["content_sm_ltks"] = rag_tokenizer.fine_grained_tokenize(d["content_ltks"])
    if "important_kwd" in req:
        if not isinstance(req["important_kwd"], list):
            return get_data_error_result(message="`important_kwd` should be a list")
        d["important_kwd"] = req["important_kwd"]
        d["important_tks"] = rag_tokenizer.tokenize(" ".join(req["important_kwd"]))
    if "question_kwd" in req:
        if not isinstance(req["question_kwd"], list):
            return get_data_error_result(message="`question_kwd` should be a list")
        d["question_kwd"] = req["question_kwd"]
        d["question_tks"] = rag_tokenizer.tokenize("\n".join(req["question_kwd"]))
    if "tag_kwd" in req:
        if not isinstance(req["tag_kwd"], list):
            return get_data_error_result(message="`tag_kwd` should be a list")
        if not all(isinstance(t, str) for t in req["tag_kwd"]):
            return get_data_error_result(message="`tag_kwd` must be a list of strings")
        d["tag_kwd"] = req["tag_kwd"]
    if "tag_feas" in req:
        try:
            d["tag_feas"] = validate_tag_features(req["tag_feas"])
        except ValueError as exc:
            return get_data_error_result(message=f"`tag_feas` {exc}")
    if "available_int" in req:
        d["available_int"] = req["available_int"]

    try:
        def _set_sync():
            tenant_id = DocumentService.get_tenant_id(req["doc_id"])
            if not tenant_id:
                return get_data_error_result(message="Tenant not found!")

            e, doc = DocumentService.get_by_id(req["doc_id"])
            if not e:
                return get_data_error_result(message="Document not found!")

            tenant_embd_id = DocumentService.get_tenant_embd_id(req["doc_id"])
            if tenant_embd_id:
                embd_model_config = get_model_config_by_id(tenant_embd_id)
            else:
                embd_id = DocumentService.get_embd_id(req["doc_id"])
                if embd_id:
                    embd_model_config = get_model_config_by_type_and_name(tenant_id, LLMType.EMBEDDING, embd_id)
                else:
                    embd_model_config = get_tenant_default_model_by_type(tenant_id, LLMType.EMBEDDING)
            embd_mdl = LLMBundle(tenant_id, embd_model_config)

            _d = d
            if doc.parser_id == ParserType.QA:
                arr = [
                    t for t in re.split(
                        r"[\n\t]",
                        req["content_with_weight"]) if len(t) > 1]
                q, a = rmPrefix(arr[0]), rmPrefix("\n".join(arr[1:]))
                _d = beAdoc(d, q, a, not any(
                    [rag_tokenizer.is_chinese(t) for t in q + a]))

            v, c = embd_mdl.encode([doc.name, content_with_weight if not _d.get("question_kwd") else "\n".join(_d["question_kwd"])])
            v = 0.1 * v[0] + 0.9 * v[1] if doc.parser_id != ParserType.QA else v[1]
            _d["q_%d_vec" % len(v)] = v.tolist()
            settings.docStoreConn.update({"id": req["chunk_id"]}, _d, search.index_name(tenant_id), doc.kb_id)

            # update image
            image_base64 = req.get("image_base64", None)
            img_id = req.get("img_id", "")
            if image_base64 and img_id and "-" in img_id:
                bkt, name = img_id.split("-", 1)
                image_binary = base64.b64decode(image_base64)
                settings.STORAGE_IMPL.put(bkt, name, image_binary)
            return get_json_result(data=True)

        return await thread_pool_exec(_set_sync)
    except Exception as e:
        return server_error_response(e)