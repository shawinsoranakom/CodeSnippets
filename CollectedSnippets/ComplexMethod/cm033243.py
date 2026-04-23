async def async_chat(dialog, messages, stream=True, **kwargs):
    logging.debug("Begin async_chat")
    assert messages[-1]["role"] == "user", "The last content of this conversation is not from user."
    use_web_search = _should_use_web_search(dialog.prompt_config, kwargs.get("internet"))
    logging.debug("web_search kb=%s tavily=%s internet=%r enabled=%s", bool(dialog.kb_ids), bool(dialog.prompt_config.get("tavily_api_key")), kwargs.get("internet"), use_web_search)
    if not dialog.kb_ids and not use_web_search:
        async for ans in async_chat_solo(dialog, messages, stream):
            yield ans
        return

    chat_start_ts = timer()
    llm_type = TenantLLMService.llm_id2llm_type(dialog.llm_id)
    if llm_type == "image2text":
        llm_model_config = TenantLLMService.get_model_config(dialog.tenant_id, LLMType.IMAGE2TEXT, dialog.llm_id)
    else:
        llm_model_config = TenantLLMService.get_model_config(dialog.tenant_id, LLMType.CHAT, dialog.llm_id)

    factory = llm_model_config.get("llm_factory", "") if llm_model_config else ""
    max_tokens = llm_model_config.get("max_tokens", 8192)

    check_llm_ts = timer()

    langfuse_tracer = None
    trace_context = {}
    langfuse_keys = TenantLangfuseService.filter_by_tenant(tenant_id=dialog.tenant_id)
    if langfuse_keys:
        langfuse = Langfuse(public_key=langfuse_keys.public_key, secret_key=langfuse_keys.secret_key, host=langfuse_keys.host)
        try:
            if langfuse.auth_check():
                langfuse_tracer = langfuse
                trace_id = langfuse_tracer.create_trace_id()
                trace_context = {"trace_id": trace_id}
        except Exception:
            # Skip langfuse tracing if connection fails
            pass

    check_langfuse_tracer_ts = timer()
    kbs, embd_mdl, rerank_mdl, chat_mdl, tts_mdl = get_models(dialog)
    toolcall_session, tools = kwargs.get("toolcall_session"), kwargs.get("tools")
    if toolcall_session and tools:
        chat_mdl.bind_tools(toolcall_session, tools)
    bind_models_ts = timer()

    retriever = settings.retriever
    questions = [m["content"] for m in messages if m["role"] == "user"][-3:]
    attachments = None
    if "doc_ids" in kwargs:
        attachments = [doc_id for doc_id in kwargs["doc_ids"].split(",") if doc_id]
    attachments_= ""
    image_attachments = []
    image_files = []
    if "doc_ids" in messages[-1]:
        attachments = [doc_id for doc_id in messages[-1]["doc_ids"] if doc_id]
    if "files" in messages[-1]:
        if llm_type == "chat":
            text_attachments, image_attachments = split_file_attachments(messages[-1]["files"])
        else:
            text_attachments, image_files = split_file_attachments(messages[-1]["files"], raw=True)
        attachments_ = "\n\n".join(text_attachments)

    prompt_config = dialog.prompt_config
    field_map = KnowledgebaseService.get_field_map(dialog.kb_ids)
    logging.debug(f"field_map retrieved: {field_map}")
    # try to use sql if field mapping is good to go
    if field_map:
        logging.debug("Use SQL to retrieval:{}".format(questions[-1]))
        ans = await use_sql(questions[-1], field_map, dialog.tenant_id, chat_mdl, prompt_config.get("quote", True), dialog.kb_ids)
        # For aggregate queries (COUNT, SUM, etc.), chunks may be empty but answer is still valid
        if ans and (ans.get("reference", {}).get("chunks") or ans.get("answer")):
            yield ans
            return
        else:
            logging.debug("SQL failed or returned no results, falling back to vector search")

    param_keys = [p["key"] for p in prompt_config.get("parameters", [])]
    if dialog.kb_ids and "knowledge" not in param_keys and "{knowledge}" in prompt_config.get("system", ""):
        logging.warning("prompt_config['parameters'] is missing 'knowledge' entry despite kb_ids being set; auto-fixing.")
        prompt_config.setdefault("parameters", []).append({"key": "knowledge", "optional": False})
        param_keys.append("knowledge")
    logging.debug(f"attachments={attachments}, param_keys={param_keys}, embd_mdl={embd_mdl}")

    for p in prompt_config.get("parameters", []):
        if p["key"] == "knowledge":
            continue
        if p["key"] not in kwargs and not p["optional"]:
            raise KeyError("Miss parameter: " + p["key"])
        if p["key"] not in kwargs:
            prompt_config["system"] = prompt_config["system"].replace("{%s}" % p["key"], " ")

    if len(questions) > 1 and prompt_config.get("refine_multiturn"):
        questions = [await full_question(dialog.tenant_id, dialog.llm_id, messages)]
    else:
        questions = questions[-1:]

    if prompt_config.get("cross_languages"):
        questions = [await cross_languages(dialog.tenant_id, dialog.llm_id, questions[0], prompt_config["cross_languages"])]

    if dialog.meta_data_filter:
        metas = DocMetadataService.get_flatted_meta_by_kbs(dialog.kb_ids)
        attachments = await apply_meta_data_filter(
            dialog.meta_data_filter,
            metas,
            questions[-1],
            chat_mdl,
            attachments,
        )

    if prompt_config.get("keyword", False):
        questions[-1] = questions[-1] + "," + await keyword_extraction(chat_mdl, questions[-1])
    refine_question_ts = timer()

    thought = ""
    kbinfos = {"total": 0, "chunks": [], "doc_aggs": []}
    knowledges = []

    if "knowledge" in param_keys:
        logging.debug("Proceeding with retrieval")
        tenant_ids = list(set([kb.tenant_id for kb in kbs]))
        knowledges = []
        if prompt_config.get("reasoning", False) or kwargs.get("reasoning"):
            reasoner = DeepResearcher(
                chat_mdl,
                prompt_config,
                partial(
                    retriever.retrieval,
                    embd_mdl=embd_mdl,
                    tenant_ids=tenant_ids,
                    kb_ids=dialog.kb_ids,
                    page=1,
                    page_size=dialog.top_n,
                    similarity_threshold=0.2,
                    vector_similarity_weight=0.3,
                    doc_ids=attachments,
                ),
                internet_enabled=use_web_search,
            )
            queue = asyncio.Queue()
            async def callback(msg:str):
                nonlocal queue
                await queue.put(msg + "<br/>")

            await callback("<START_DEEP_RESEARCH>")
            task = asyncio.create_task(reasoner.research(kbinfos, questions[-1], questions[-1], callback=callback))
            while True:
                msg = await queue.get()
                if msg.find("<START_DEEP_RESEARCH>") == 0:
                    yield {"answer": "", "reference": {}, "audio_binary": None, "final": False, "start_to_think": True}
                elif msg.find("<END_DEEP_RESEARCH>") == 0:
                    yield {"answer": "", "reference": {}, "audio_binary": None, "final": False, "end_to_think": True}
                    break
                else:
                    yield {"answer": msg, "reference": {}, "audio_binary": None, "final": False}

            await task

        else:
            if embd_mdl:
                kbinfos = await retriever.retrieval(
                    " ".join(questions),
                    embd_mdl,
                    tenant_ids,
                    dialog.kb_ids,
                    1,
                    dialog.top_n,
                    dialog.similarity_threshold,
                    dialog.vector_similarity_weight,
                    doc_ids=attachments,
                    top=dialog.top_k,
                    aggs=True,
                    rerank_mdl=rerank_mdl,
                    rank_feature=label_question(" ".join(questions), kbs),
                )
                if prompt_config.get("toc_enhance"):
                    cks = await retriever.retrieval_by_toc(" ".join(questions), kbinfos["chunks"], tenant_ids, chat_mdl, dialog.top_n)
                    if cks:
                        kbinfos["chunks"] = cks
                kbinfos["chunks"] = retriever.retrieval_by_children(kbinfos["chunks"], tenant_ids)
            if use_web_search:
                tav = Tavily(prompt_config["tavily_api_key"])
                tav_res = tav.retrieve_chunks(" ".join(questions))
                kbinfos["chunks"].extend(tav_res["chunks"])
                kbinfos["doc_aggs"].extend(tav_res["doc_aggs"])
            if prompt_config.get("use_kg"):
                default_chat_model = get_tenant_default_model_by_type(dialog.tenant_id, LLMType.CHAT)
                ck = await settings.kg_retriever.retrieval(" ".join(questions), tenant_ids, dialog.kb_ids, embd_mdl,
                                                       LLMBundle(dialog.tenant_id, default_chat_model))
                if ck["content_with_weight"]:
                    kbinfos["chunks"].insert(0, ck)

    knowledges = kb_prompt(kbinfos, max_tokens)
    logging.debug("{}->{}".format(" ".join(questions), "\n->".join(knowledges)))

    retrieval_ts = timer()
    if not knowledges and prompt_config.get("empty_response"):
        empty_res = prompt_config["empty_response"]
        yield {"answer": empty_res, "reference": kbinfos, "prompt": "\n\n### Query:\n%s" % " ".join(questions),
               "audio_binary": tts(tts_mdl, empty_res), "final": True}
        return

    kwargs["knowledge"] = "\n------\n" + "\n\n------\n\n".join(knowledges)
    gen_conf = dialog.llm_setting

    msg = [{"role": "system", "content": prompt_config["system"].format(**kwargs)+attachments_}]
    prompt4citation = ""
    if knowledges and (prompt_config.get("quote", True) and kwargs.get("quote", True)):
        prompt4citation = citation_prompt()
    msg.extend([{"role": m["role"], "content": re.sub(r"##\d+\$\$", "", m["content"])} for m in messages if m["role"] != "system"])
    used_token_count, msg = message_fit_in(msg, int(max_tokens * 0.95))
    if llm_type == "chat" and image_attachments:
        convert_last_user_msg_to_multimodal(msg, image_attachments, factory)
    assert len(msg) >= 2, f"message_fit_in has bug: {msg}"
    prompt = msg[0]["content"]

    if "max_tokens" in gen_conf:
        gen_conf["max_tokens"] = min(gen_conf["max_tokens"], max_tokens - used_token_count)

    def decorate_answer(answer):
        nonlocal embd_mdl, prompt_config, knowledges, kwargs, kbinfos, prompt, retrieval_ts, questions, langfuse_tracer

        refs = []
        ans = answer.split("</think>")
        think = ""
        if len(ans) == 2:
            think = ans[0] + "</think>"
            answer = ans[1]

        if knowledges and (prompt_config.get("quote", True) and kwargs.get("quote", True)):
            idx = set([])
            normalized_answer = normalize_arabic_digits(answer) or ""
            if embd_mdl and not CITATION_MARKER_PATTERN.search(normalized_answer):
                answer, idx = retriever.insert_citations(
                    answer,
                    [ck["content_ltks"] for ck in kbinfos["chunks"]],
                    [ck["vector"] for ck in kbinfos["chunks"]],
                    embd_mdl,
                    tkweight=1 - dialog.vector_similarity_weight,
                    vtweight=dialog.vector_similarity_weight,
                )
            else:
                for match in CITATION_MARKER_PATTERN.finditer(normalized_answer):
                    i = int(match.group(1))
                    if i < len(kbinfos["chunks"]):
                        idx.add(i)

            answer, idx = repair_bad_citation_formats(answer, kbinfos, idx)

            idx = set([kbinfos["chunks"][int(i)]["doc_id"] for i in idx])
            recall_docs = [d for d in kbinfos["doc_aggs"] if d["doc_id"] in idx]
            if not recall_docs:
                recall_docs = kbinfos["doc_aggs"]
            kbinfos["doc_aggs"] = recall_docs

            refs = deepcopy(kbinfos)
            for c in refs["chunks"]:
                if c.get("vector"):
                    del c["vector"]

        if answer.lower().find("invalid key") >= 0 or answer.lower().find("invalid api") >= 0:
            answer += " Please set LLM API-Key in 'User Setting -> Model providers -> API-Key'"
        finish_chat_ts = timer()

        total_time_cost = (finish_chat_ts - chat_start_ts) * 1000
        check_llm_time_cost = (check_llm_ts - chat_start_ts) * 1000
        check_langfuse_tracer_cost = (check_langfuse_tracer_ts - check_llm_ts) * 1000
        bind_embedding_time_cost = (bind_models_ts - check_langfuse_tracer_ts) * 1000
        refine_question_time_cost = (refine_question_ts - bind_models_ts) * 1000
        retrieval_time_cost = (retrieval_ts - refine_question_ts) * 1000
        generate_result_time_cost = (finish_chat_ts - retrieval_ts) * 1000

        tk_num = num_tokens_from_string(think + answer)
        prompt += "\n\n### Query:\n%s" % " ".join(questions)
        prompt = (
            f"{prompt}\n\n"
            "## Time elapsed:\n"
            f"  - Total: {total_time_cost:.1f}ms\n"
            f"  - Check LLM: {check_llm_time_cost:.1f}ms\n"
            f"  - Check Langfuse tracer: {check_langfuse_tracer_cost:.1f}ms\n"
            f"  - Bind models: {bind_embedding_time_cost:.1f}ms\n"
            f"  - Query refinement(LLM): {refine_question_time_cost:.1f}ms\n"
            f"  - Retrieval: {retrieval_time_cost:.1f}ms\n"
            f"  - Generate answer: {generate_result_time_cost:.1f}ms\n\n"
            "## Token usage:\n"
            f"  - Generated tokens(approximately): {tk_num}\n"
            f"  - Token speed: {int(tk_num / (generate_result_time_cost / 1000.0))}/s"
        )

        # Add a condition check to call the end method only if langfuse_tracer exists
        if langfuse_tracer and "langfuse_generation" in locals():
            langfuse_output = "\n" + re.sub(r"^.*?(### Query:.*)", r"\1", prompt, flags=re.DOTALL)
            langfuse_output = {"time_elapsed:": re.sub(r"\n", "  \n", langfuse_output), "created_at": time.time()}
            langfuse_generation.update(output=langfuse_output)
            langfuse_generation.end()

        return {"answer": think + answer, "reference": refs, "prompt": re.sub(r"\n", "  \n", prompt), "created_at": time.time()}

    if langfuse_tracer:
        langfuse_generation = langfuse_tracer.start_generation(
            trace_context=trace_context, name="chat", model=llm_model_config["llm_name"],
            input={"prompt": prompt, "prompt4citation": prompt4citation, "messages": msg}
        )

    if stream:
        if llm_type == "chat":
            stream_iter = chat_mdl.async_chat_streamly_delta(prompt + prompt4citation, msg[1:], gen_conf)
        else:
            stream_iter = chat_mdl.async_chat_streamly_delta(prompt + prompt4citation, msg[1:], gen_conf, images=image_files)
        last_state = None
        async for kind, value, state in _stream_with_think_delta(stream_iter):
            last_state = state
            if kind == "marker":
                flags = {"start_to_think": True} if value == "<think>" else {"end_to_think": True}
                yield {"answer": "", "reference": {}, "audio_binary": None, "final": False, **flags}
                continue
            yield {"answer": value, "reference": {}, "audio_binary": tts(tts_mdl, value), "final": False}
        full_answer = last_state.full_text if last_state else ""
        if full_answer:
            final = decorate_answer(_extract_visible_answer(thought + full_answer))
            final["final"] = True
            final["audio_binary"] = None
            yield final
    else:
        if llm_type == "chat":
            answer = await chat_mdl.async_chat(prompt + prompt4citation, msg[1:], gen_conf)
        else:
            answer = await chat_mdl.async_chat(prompt + prompt4citation, msg[1:], gen_conf, images=image_files)
        user_content = msg[-1].get("content", "[content not available]")
        logging.debug("User: {}|Assistant: {}".format(user_content, answer))
        res = decorate_answer(answer)
        res["audio_binary"] = tts(tts_mdl, answer)
        yield res

    return