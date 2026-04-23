async def run_dataflow(task: dict):
    from api.db.services.canvas_service import UserCanvasService
    from rag.flow.pipeline import Pipeline

    task_start_ts = timer()
    dataflow_id = task["dataflow_id"]
    doc_id = task["doc_id"]
    task_id = task["id"]
    task_dataset_id = task["kb_id"]

    if task["task_type"] == "dataflow":
        e, cvs = UserCanvasService.get_by_id(dataflow_id)
        assert e, "User pipeline not found."
        dsl = cvs.dsl
    else:
        e, pipeline_log = PipelineOperationLogService.get_by_id(dataflow_id)
        assert e, "Pipeline log not found."
        dsl = pipeline_log.dsl
        dataflow_id = pipeline_log.pipeline_id
    pipeline = Pipeline(dsl, tenant_id=task["tenant_id"], doc_id=doc_id, task_id=task_id, flow_id=dataflow_id)
    chunks = await pipeline.run(file=task["file"]) if task.get("file") else await pipeline.run()
    if doc_id == CANVAS_DEBUG_DOC_ID:
        return

    if not chunks:
        PipelineOperationLogService.create(document_id=doc_id, pipeline_id=dataflow_id,
                                           task_type=PipelineTaskType.PARSE, dsl=str(pipeline))
        return

    embedding_token_consumption = chunks.get("embedding_token_consumption", 0)
    # The output key may exist with an empty payload; check presence, not truthiness.
    if "chunks" in chunks:
        chunks = copy.deepcopy(chunks["chunks"])
    elif "json" in chunks:
        chunks = copy.deepcopy(chunks["json"])
    elif "markdown" in chunks:
        chunks = [{"text": [chunks["markdown"]]}] if chunks["markdown"] else []
    elif "text" in chunks:
        chunks = [{"text": [chunks["text"]]}] if chunks["text"] else []
    elif "html" in chunks:
        chunks = [{"text": [chunks["html"]]}] if chunks["html"] else []
    else:
        chunks = []

    # An empty normalized payload means "nothing parsed", so stop before embedding/indexing.
    if not chunks:
        PipelineOperationLogService.create(document_id=doc_id, pipeline_id=dataflow_id,
                                           task_type=PipelineTaskType.PARSE, dsl=str(pipeline))
        return

    keys = [k for o in chunks for k in list(o.keys())]
    if not any([re.match(r"q_[0-9]+_vec", k) for k in keys]):
        try:
            set_progress(task_id, prog=0.82, msg="\n-------------------------------------\nStart to embedding...")
            e, kb = KnowledgebaseService.get_by_id(task["kb_id"])
            embedding_id = kb.embd_id
            embd_model_config = get_model_config_by_type_and_name(task["tenant_id"], LLMType.EMBEDDING, embedding_id)
            embedding_model = LLMBundle(task["tenant_id"], embd_model_config)

            @timeout(60)
            def batch_encode(txts):
                nonlocal embedding_model
                return embedding_model.encode([truncate(c, embedding_model.max_length - 10) for c in txts])

            vects = np.array([])
            texts = [o.get("questions", o.get("summary", o["text"])) for o in chunks]
            delta = 0.20 / (len(texts) // settings.EMBEDDING_BATCH_SIZE + 1)
            prog = 0.8
            for i in range(0, len(texts), settings.EMBEDDING_BATCH_SIZE):
                async with embed_limiter:
                    vts, c = await thread_pool_exec(batch_encode, texts[i: i + settings.EMBEDDING_BATCH_SIZE])
                if len(vects) == 0:
                    vects = vts
                else:
                    vects = np.concatenate((vects, vts), axis=0)
                embedding_token_consumption += c
                prog += delta
                if i % (len(texts) // settings.EMBEDDING_BATCH_SIZE / 100 + 1) == 1:
                    set_progress(task_id, prog=prog, msg=f"{i + 1} / {len(texts) // settings.EMBEDDING_BATCH_SIZE}")

            assert len(vects) == len(chunks)
            for i, ck in enumerate(chunks):
                v = vects[i].tolist()
                ck["q_%d_vec" % len(v)] = v
        except TaskCanceledException:
            raise
        except Exception as e:
            set_progress(task_id, prog=-1, msg=f"[ERROR]: {e}")
            PipelineOperationLogService.create(document_id=doc_id, pipeline_id=dataflow_id,
                                               task_type=PipelineTaskType.PARSE, dsl=str(pipeline))
            return

    metadata = {}
    for ck in chunks:
        ck["doc_id"] = doc_id
        ck["kb_id"] = [str(task["kb_id"])]
        ck["docnm_kwd"] = task["name"]
        ck["create_time"] = str(datetime.now()).replace("T", " ")[:19]
        ck["create_timestamp_flt"] = datetime.now().timestamp()
        if not ck.get("id"):
            ck["id"] = xxhash.xxh64((ck["text"] + str(ck["doc_id"])).encode("utf-8")).hexdigest()
        if "questions" in ck:
            if "question_tks" not in ck:
                ck["question_kwd"] = ck["questions"].split("\n")
                ck["question_tks"] = rag_tokenizer.tokenize(str(ck["questions"]))
            del ck["questions"]
        if "keywords" in ck:
            if "important_tks" not in ck:
                ck["important_kwd"] = ck["keywords"].split(",")
                ck["important_tks"] = rag_tokenizer.tokenize(str(ck["keywords"]))
            del ck["keywords"]
        if "summary" in ck:
            if "content_ltks" not in ck:
                ck["content_ltks"] = rag_tokenizer.tokenize(str(ck["summary"]))
                ck["content_sm_ltks"] = rag_tokenizer.fine_grained_tokenize(ck["content_ltks"])
            del ck["summary"]
        if "metadata" in ck:
            metadata = update_metadata_to(metadata, ck["metadata"])
            del ck["metadata"]
        if "content_with_weight" not in ck:
            ck["content_with_weight"] = ck["text"]
        del ck["text"]
        if "positions" in ck:
            add_positions(ck, ck["positions"])
            del ck["positions"]

    if metadata:
        existing_meta = DocMetadataService.get_document_metadata(doc_id)
        existing_meta = existing_meta if isinstance(existing_meta, dict) else {}
        metadata = update_metadata_to(metadata, existing_meta)
        DocMetadataService.update_document_metadata(doc_id, metadata)

    start_ts = timer()
    set_progress(task_id, prog=0.82, msg="[DOC Engine]:\nStart to index...")
    e = await insert_chunks(task_id, task["tenant_id"], task["kb_id"], chunks, partial(set_progress, task_id, 0, 100000000))
    if not e:
        PipelineOperationLogService.create(document_id=doc_id, pipeline_id=dataflow_id,
                                           task_type=PipelineTaskType.PARSE, dsl=str(pipeline))
        return

    time_cost = timer() - start_ts
    task_time_cost = timer() - task_start_ts
    set_progress(task_id, prog=1., msg="Indexing done ({:.2f}s). Task done ({:.2f}s)".format(time_cost, task_time_cost))
    DocumentService.increment_chunk_num(doc_id, task_dataset_id, embedding_token_consumption, len(chunks),
                                        task_time_cost)
    logging.info("[Done], chunks({}), token({}), elapsed:{:.2f}".format(len(chunks), embedding_token_consumption,
                                                                        task_time_cost))
    PipelineOperationLogService.create(document_id=doc_id, pipeline_id=dataflow_id, task_type=PipelineTaskType.PARSE,
                                       dsl=str(pipeline))