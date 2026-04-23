async def create():
    req = await get_request_json()
    req_id = request.headers.get("X-Request-ID")
    chunck_id = xxhash.xxh64((req["content_with_weight"] + req["doc_id"]).encode("utf-8")).hexdigest()
    d = {"id": chunck_id, "content_ltks": rag_tokenizer.tokenize(req["content_with_weight"]),
         "content_with_weight": req["content_with_weight"]}
    d["content_sm_ltks"] = rag_tokenizer.fine_grained_tokenize(d["content_ltks"])
    d["important_kwd"] = req.get("important_kwd", [])
    if not isinstance(d["important_kwd"], list):
        return get_data_error_result(message="`important_kwd` is required to be a list")
    d["important_tks"] = rag_tokenizer.tokenize(" ".join(d["important_kwd"]))
    d["question_kwd"] = req.get("question_kwd", [])
    if not isinstance(d["question_kwd"], list):
        return get_data_error_result(message="`question_kwd` is required to be a list")
    d["question_tks"] = rag_tokenizer.tokenize("\n".join(d["question_kwd"]))
    d["create_time"] = str(datetime.datetime.now()).replace("T", " ")[:19]
    d["create_timestamp_flt"] = datetime.datetime.now().timestamp()
    if "tag_kwd" in req:
        if not isinstance(req["tag_kwd"], list):
            return get_data_error_result(message="`tag_kwd` is required to be a list")
        if not all(isinstance(t, str) for t in req["tag_kwd"]):
            return get_data_error_result(message="`tag_kwd` must be a list of strings")
        d["tag_kwd"] = req["tag_kwd"]
    if "tag_feas" in req:
        try:
            d["tag_feas"] = validate_tag_features(req["tag_feas"])
        except ValueError as exc:
            return get_data_error_result(message=f"`tag_feas` {exc}")
    image_base64 = req.get("image_base64", None)

    try:
        def _log_response(resp, code, message):
            logging.info(
                "chunk_create response req_id=%s status=%s code=%s message=%s",
                req_id,
                getattr(resp, "status_code", None),
                code,
                message,
            )

        def _create_sync():
            e, doc = DocumentService.get_by_id(req["doc_id"])
            if not e:
                resp = get_data_error_result(message="Document not found!")
                _log_response(resp, RetCode.DATA_ERROR, "Document not found!")
                return resp
            d["kb_id"] = [doc.kb_id]
            d["docnm_kwd"] = doc.name
            d["title_tks"] = rag_tokenizer.tokenize(doc.name)
            d["doc_id"] = doc.id

            tenant_id = DocumentService.get_tenant_id(req["doc_id"])
            if not tenant_id:
                resp = get_data_error_result(message="Tenant not found!")
                _log_response(resp, RetCode.DATA_ERROR, "Tenant not found!")
                return resp

            e, kb = KnowledgebaseService.get_by_id(doc.kb_id)
            if not e:
                resp = get_data_error_result(message="Knowledgebase not found!")
                _log_response(resp, RetCode.DATA_ERROR, "Knowledgebase not found!")
                return resp
            if kb.pagerank:
                d[PAGERANK_FLD] = kb.pagerank

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

            if image_base64:
                d["img_id"] = "{}-{}".format(doc.kb_id, chunck_id)
                d["doc_type_kwd"] = "image"

            v, c = embd_mdl.encode([doc.name, req["content_with_weight"] if not d["question_kwd"] else "\n".join(d["question_kwd"])])
            v = 0.1 * v[0] + 0.9 * v[1]
            d["q_%d_vec" % len(v)] = v.tolist()
            settings.docStoreConn.insert([d], search.index_name(tenant_id), doc.kb_id)

            if image_base64:
                store_chunk_image(doc.kb_id, chunck_id, base64.b64decode(image_base64))

            DocumentService.increment_chunk_num(
                doc.id, doc.kb_id, c, 1, 0)
            resp = get_json_result(data={"chunk_id": chunck_id, "image_id": d.get("img_id", "")})
            _log_response(resp, RetCode.SUCCESS, "success")
            return resp

        return await thread_pool_exec(_create_sync)
    except Exception as e:
        logging.info("chunk_create exception req_id=%s error=%r", req_id, e)
        return server_error_response(e)