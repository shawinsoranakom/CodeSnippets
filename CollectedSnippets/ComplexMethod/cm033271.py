def doc_upload_and_parse(conversation_id, file_objs, user_id):
    from api.db.services.api_service import API4ConversationService
    from api.db.services.conversation_service import ConversationService
    from api.db.services.dialog_service import DialogService
    from api.db.services.file_service import FileService
    from api.db.services.llm_service import LLMBundle
    from api.db.services.user_service import TenantService
    from api.db.joint_services.tenant_model_service import get_model_config_by_id, get_model_config_by_type_and_name, get_tenant_default_model_by_type
    from rag.app import audio, email, naive, picture, presentation

    e, conv = ConversationService.get_by_id(conversation_id)
    if not e:
        e, conv = API4ConversationService.get_by_id(conversation_id)
    assert e, "Conversation not found!"

    e, dia = DialogService.get_by_id(conv.dialog_id)
    if not dia.kb_ids:
        raise LookupError("No dataset associated with this conversation. Please add a dataset before uploading documents")
    kb_id = dia.kb_ids[0]
    e, kb = KnowledgebaseService.get_by_id(kb_id)
    if not e:
        raise LookupError("Can't find this dataset!")
    if kb.tenant_embd_id:
        embd_model_config = get_model_config_by_id(kb.tenant_embd_id)
    else:
        embd_model_config = get_model_config_by_type_and_name(kb.tenant_id, LLMType.EMBEDDING, kb.embd_id)
    embd_mdl = LLMBundle(kb.tenant_id, embd_model_config, lang=kb.language)

    err, files = FileService.upload_document(kb, file_objs, user_id)
    assert not err, "\n".join(err)

    def dummy(prog=None, msg=""):
        pass

    FACTORY = {ParserType.PRESENTATION.value: presentation, ParserType.PICTURE.value: picture, ParserType.AUDIO.value: audio, ParserType.EMAIL.value: email}
    parser_config = {"chunk_token_num": 4096, "delimiter": "\n!?;。；！？", "layout_recognize": "Plain Text", "table_context_size": 0, "image_context_size": 0}
    exe = ThreadPoolExecutor(max_workers=12)
    threads = []
    doc_nm = {}
    for d, blob in files:
        doc_nm[d["id"]] = d["name"]
    for d, blob in files:
        kwargs = {"callback": dummy, "parser_config": parser_config, "from_page": 0, "to_page": 100000, "tenant_id": kb.tenant_id, "lang": kb.language}
        threads.append(exe.submit(FACTORY.get(d["parser_id"], naive).chunk, d["name"], blob, **kwargs))

    for (docinfo, _), th in zip(files, threads):
        docs = []
        doc = {"doc_id": docinfo["id"], "kb_id": [kb.id]}
        for ck in th.result():
            d = deepcopy(doc)
            d.update(ck)
            d["id"] = xxhash.xxh64((ck["content_with_weight"] + str(d["doc_id"])).encode("utf-8")).hexdigest()
            d["create_time"] = str(datetime.now()).replace("T", " ")[:19]
            d["create_timestamp_flt"] = datetime.now().timestamp()
            if not d.get("image"):
                docs.append(d)
                continue

            output_buffer = BytesIO()
            if isinstance(d["image"], bytes):
                output_buffer = BytesIO(d["image"])
            else:
                d["image"].save(output_buffer, format="JPEG")

            settings.STORAGE_IMPL.put(kb.id, d["id"], output_buffer.getvalue())
            d["img_id"] = "{}-{}".format(kb.id, d["id"])
            d.pop("image", None)
            docs.append(d)

    parser_ids = {d["id"]: d["parser_id"] for d, _ in files}
    docids = [d["id"] for d, _ in files]
    chunk_counts = {id: 0 for id in docids}
    token_counts = {id: 0 for id in docids}
    es_bulk_size = 64

    def embedding(doc_id, cnts, batch_size=16):
        nonlocal embd_mdl, chunk_counts, token_counts
        vectors = []
        for i in range(0, len(cnts), batch_size):
            vts, c = embd_mdl.encode(cnts[i : i + batch_size])
            vectors.extend(vts.tolist())
            chunk_counts[doc_id] += len(cnts[i : i + batch_size])
            token_counts[doc_id] += c
        return vectors

    idxnm = search.index_name(kb.tenant_id)
    try_create_idx = True

    _, tenant = TenantService.get_by_id(kb.tenant_id)
    tenant_llm_config = get_tenant_default_model_by_type(kb.tenant_id, LLMType.CHAT)
    llm_bdl = LLMBundle(kb.tenant_id, tenant_llm_config)
    for doc_id in docids:
        cks = [c for c in docs if c["doc_id"] == doc_id]

        if parser_ids[doc_id] != ParserType.PICTURE.value:
            from rag.graphrag.general.mind_map_extractor import MindMapExtractor

            mindmap = MindMapExtractor(llm_bdl)
            try:
                mind_map = asyncio.run(mindmap([c["content_with_weight"] for c in docs if c["doc_id"] == doc_id]))
                mind_map = json.dumps(mind_map.output, ensure_ascii=False, indent=2)
                if len(mind_map) < 32:
                    raise Exception("Few content: " + mind_map)
                cks.append(
                    {
                        "id": get_uuid(),
                        "doc_id": doc_id,
                        "kb_id": [kb.id],
                        "docnm_kwd": doc_nm[doc_id],
                        "title_tks": rag_tokenizer.tokenize(re.sub(r"\.[a-zA-Z]+$", "", doc_nm[doc_id])),
                        "content_ltks": rag_tokenizer.tokenize("summary summarize 总结 概况 file 文件 概括"),
                        "content_with_weight": mind_map,
                        "knowledge_graph_kwd": "mind_map",
                    }
                )
            except Exception:
                logging.exception("Mind map generation error")

        vectors = embedding(doc_id, [c["content_with_weight"] for c in cks])
        assert len(cks) == len(vectors)
        for i, d in enumerate(cks):
            v = vectors[i]
            d["q_%d_vec" % len(v)] = v
        for b in range(0, len(cks), es_bulk_size):
            if try_create_idx:
                if not settings.docStoreConn.index_exist(idxnm, kb_id):
                    settings.docStoreConn.create_idx(idxnm, kb_id, len(vectors[0]), kb.parser_id)
                try_create_idx = False
            settings.docStoreConn.insert(cks[b : b + es_bulk_size], idxnm, kb_id)

        DocumentService.increment_chunk_num(doc_id, kb.id, token_counts[doc_id], chunk_counts[doc_id], 0)

    return [d["id"] for d, _ in files]