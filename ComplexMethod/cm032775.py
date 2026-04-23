async def do_handle_task(task):
    task_type = task.get("task_type", "")

    if task_type == "memory":
        await handle_save_to_memory_task(task)
        return

    if task_type == "dataflow" and task.get("doc_id", "") == CANVAS_DEBUG_DOC_ID:
        await run_dataflow(task)
        return

    task_id = task["id"]
    task_from_page = task["from_page"]
    task_to_page = task["to_page"]
    task_tenant_id = task["tenant_id"]
    task_embedding_id = task["embd_id"]
    task_language = task["language"]
    doc_task_llm_id = task["parser_config"].get("llm_id") or task["llm_id"]
    kb_task_llm_id = task['kb_parser_config'].get("llm_id") or task["llm_id"]
    task['llm_id'] = kb_task_llm_id
    task_dataset_id = task["kb_id"]
    task_doc_id = task["doc_id"]
    task_document_name = task["name"]
    task_parser_config = task["parser_config"]
    task_start_ts = timer()
    toc_thread = None
    executor = concurrent.futures.ThreadPoolExecutor()

    # prepare the progress callback function
    progress_callback = partial(set_progress, task_id, task_from_page, task_to_page)

    task_canceled = has_canceled(task_id)
    if task_canceled:
        progress_callback(-1, msg="Task has been canceled.")
        return

    try:
        # bind embedding model
        if task_embedding_id:
            embd_model_config = get_model_config_by_type_and_name(task_tenant_id, LLMType.EMBEDDING, task_embedding_id)
        else:
            embd_model_config = get_tenant_default_model_by_type(task_tenant_id, LLMType.EMBEDDING)
        embedding_model = LLMBundle(task_tenant_id, embd_model_config, lang=task_language)
        vts, _ = embedding_model.encode(["ok"])
        vector_size = len(vts[0])
    except Exception as e:
        error_message = f'Fail to bind embedding model: {str(e)}'
        progress_callback(-1, msg=error_message)
        logging.exception(error_message)
        raise

    init_kb(task, vector_size)

    if task_type[:len("dataflow")] == "dataflow":
        await run_dataflow(task)
        return

    if task_type == "raptor":
        ok, kb = KnowledgebaseService.get_by_id(task_dataset_id)
        if not ok:
            progress_callback(prog=-1.0, msg="Cannot found valid dataset for RAPTOR task")
            return

        kb_parser_config = kb.parser_config
        if not kb_parser_config.get("raptor", {}).get("use_raptor", False):
            kb_parser_config.update(
                {
                    "raptor": {
                        "use_raptor": True,
                        "prompt": "Please summarize the following paragraphs. Be careful with the numbers, do not make things up. Paragraphs as following:\n      {cluster_content}\nThe above is the content you need to summarize.",
                        "max_token": 256,
                        "threshold": 0.1,
                        "max_cluster": 64,
                        "random_seed": 0,
                        "scope": "file"
                    },
                }
            )
            if not KnowledgebaseService.update_by_id(kb.id, {"parser_config": kb_parser_config}):
                progress_callback(prog=-1.0, msg="Internal error: Invalid RAPTOR configuration")
                return

        # Check if Raptor should be skipped for structured data
        file_type = task.get("type", "")
        parser_id = task.get("parser_id", "")
        raptor_config = kb_parser_config.get("raptor", {})

        if should_skip_raptor(file_type, parser_id, task_parser_config, raptor_config):
            skip_reason = get_skip_reason(file_type, parser_id, task_parser_config)
            logging.info(f"Skipping Raptor for document {task_document_name}: {skip_reason}")
            progress_callback(prog=1.0, msg=f"Raptor skipped: {skip_reason}")
            return

        # bind LLM for raptor
        chat_model_config = get_model_config_by_type_and_name(task_tenant_id, LLMType.CHAT, kb_task_llm_id)
        chat_model = LLMBundle(task_tenant_id, chat_model_config, lang=task_language)
        # run RAPTOR
        async with kg_limiter:
            chunks, token_count = await run_raptor_for_kb(
                row=task,
                kb_parser_config=kb_parser_config,
                chat_mdl=chat_model,
                embd_mdl=embedding_model,
                vector_size=vector_size,
                callback=progress_callback,
                doc_ids=task.get("doc_ids", []),
            )
        if fake_doc_ids := task.get("doc_ids", []):
            task_doc_id = fake_doc_ids[0]  # use the first document ID to represent this task for logging purposes
    # Either using graphrag or Standard chunking methods
    elif task_type == "graphrag":
        ok, kb = KnowledgebaseService.get_by_id(task_dataset_id)
        if not ok:
            progress_callback(prog=-1.0, msg="Cannot found valid dataset for GraphRAG task")
            return

        kb_parser_config = kb.parser_config
        if not kb_parser_config.get("graphrag", {}).get("use_graphrag", False):
            kb_parser_config.update(
                {
                    "graphrag": {
                        "use_graphrag": True,
                        "entity_types": [
                            "organization",
                            "person",
                            "geo",
                            "event",
                            "category",
                        ],
                        "method": "light",
                    }
                }
            )
            if not KnowledgebaseService.update_by_id(kb.id, {"parser_config": kb_parser_config}):
                progress_callback(prog=-1.0, msg="Internal error: Invalid GraphRAG configuration")
                return

        graphrag_conf = kb_parser_config.get("graphrag", {})
        start_ts = timer()
        chat_model_config = get_model_config_by_type_and_name(task_tenant_id, LLMType.CHAT, kb_task_llm_id)
        chat_model = LLMBundle(task_tenant_id, chat_model_config, lang=task_language)
        with_resolution = graphrag_conf.get("resolution", False)
        with_community = graphrag_conf.get("community", False)
        async with kg_limiter:
            # await run_graphrag(task, task_language, with_resolution, with_community, chat_model, embedding_model, progress_callback)
            result = await run_graphrag_for_kb(
                row=task,
                doc_ids=task.get("doc_ids", []),
                language=task_language,
                kb_parser_config=kb_parser_config,
                chat_model=chat_model,
                embedding_model=embedding_model,
                callback=progress_callback,
                with_resolution=with_resolution,
                with_community=with_community,
            )
            logging.info(f"GraphRAG task result for task {task}:\n{result}")
        progress_callback(prog=1.0, msg="Knowledge Graph done ({:.2f}s)".format(timer() - start_ts))
        return
    elif task_type == "mindmap":
        progress_callback(1, "place holder")
        pass
        return
    else:
        # Standard chunking methods
        task['llm_id'] = doc_task_llm_id
        start_ts = timer()
        chunks = await build_chunks(task, progress_callback)
        logging.info("Build document {}: {:.2f}s".format(task_document_name, timer() - start_ts))
        if not chunks:
            progress_callback(1., msg=f"No chunk built from {task_document_name}")
            return
        progress_callback(msg="Generate {} chunks".format(len(chunks)))
        start_ts = timer()
        try:
            token_count, vector_size = await embedding(chunks, embedding_model, task_parser_config, progress_callback)
        except TaskCanceledException:
            raise
        except Exception as e:
            error_message = "Generate embedding error:{}".format(str(e))
            progress_callback(-1, error_message)
            logging.exception(error_message)
            token_count = 0
            raise
        progress_message = "Embedding chunks ({:.2f}s)".format(timer() - start_ts)
        logging.info(progress_message)
        progress_callback(msg=progress_message)
        if task["parser_id"].lower() == "naive" and task["parser_config"].get("toc_extraction", False):
            toc_thread = executor.submit(build_TOC, task, chunks, progress_callback)

    chunk_count = len(set([chunk["id"] for chunk in chunks]))
    start_ts = timer()

    async def _maybe_insert_chunks(_chunks):
        if has_canceled(task_id):
            progress_callback(-1, msg="Task has been canceled.")
            return False
        insert_result = await insert_chunks(task_id, task_tenant_id, task_dataset_id, _chunks, progress_callback)
        return bool(insert_result)

    try:
        if not await _maybe_insert_chunks(chunks):
            return
        if has_canceled(task_id):
            progress_callback(-1, msg="Task has been canceled.")
            return

        logging.info(
            "Indexing doc({}), page({}-{}), chunks({}), elapsed: {:.2f}".format(
                task_document_name, task_from_page, task_to_page, len(chunks), timer() - start_ts
            )
        )

        DocumentService.increment_chunk_num(task_doc_id, task_dataset_id, token_count, chunk_count, 0)

        progress_callback(msg="Indexing done ({:.2f}s).".format(timer() - start_ts))

        if toc_thread:
            d = toc_thread.result()
            if d:
                if not await _maybe_insert_chunks([d]):
                    return
                DocumentService.increment_chunk_num(task_doc_id, task_dataset_id, 0, 1, 0)

        if has_canceled(task_id):
            progress_callback(-1, msg="Task has been canceled.")
            return

        task_time_cost = timer() - task_start_ts
        progress_callback(prog=1.0, msg="Task done ({:.2f}s)".format(task_time_cost))
        logging.info(
            "Chunk doc({}), page({}-{}), chunks({}), token({}), elapsed:{:.2f}".format(
                task_document_name, task_from_page, task_to_page, len(chunks), token_count, task_time_cost
            )
        )

    finally:
        if has_canceled(task_id):
            try:
                exists = await thread_pool_exec(
                    settings.docStoreConn.index_exist,
                    search.index_name(task_tenant_id),
                    task_dataset_id,
                )
                if exists:
                    await thread_pool_exec(
                        settings.docStoreConn.delete,
                        {"doc_id": task_doc_id},
                        search.index_name(task_tenant_id),
                        task_dataset_id,
                    )
            except Exception as e:
                logging.exception(
                    f"Remove doc({task_doc_id}) from docStore failed when task({task_id}) canceled, exception: {e}")