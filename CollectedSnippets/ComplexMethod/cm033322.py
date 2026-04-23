async def set_api_key():
    req = await get_request_json()
    # test if api key works
    chat_passed, embd_passed, rerank_passed = False, False, False
    factory = req["llm_factory"]
    base_url = req.get("base_url", "")
    source_factory = req.get("source_fid", factory)
    extra = {"provider": factory}
    timeout_seconds = int(os.environ.get("LLM_TIMEOUT_SECONDS", 10))
    source_llms = list(LLMService.query(fid=source_factory))
    if not source_llms:
        msg = f"No models configured for {factory} (source: {source_factory})."
        if req.get("verify", False):
            return get_json_result(data={"message": msg, "success": False})
        return get_data_error_result(message=msg)

    msg = ""
    for llm in source_llms:
        if not embd_passed and llm.model_type == LLMType.EMBEDDING.value:
            assert factory in EmbeddingModel, f"Embedding model from {factory} is not supported yet."
            mdl = EmbeddingModel[factory](req["api_key"], llm.llm_name, base_url=base_url)
            try:
                arr, tc = await asyncio.wait_for(
                    asyncio.to_thread(mdl.encode, ["Test if the api key is available"]),
                    timeout=timeout_seconds,
                )
                if len(arr[0]) == 0:
                    raise Exception("Fail")
                embd_passed = True
            except Exception as e:
                msg += f"\nFail to access embedding model({llm.llm_name}) using this api key." + str(e)
        elif not chat_passed and llm.model_type == LLMType.CHAT.value:
            assert factory in ChatModel, f"Chat model from {factory} is not supported yet."
            mdl = ChatModel[factory](req["api_key"], llm.llm_name, base_url=base_url, **extra)
            try:
                async def check_streamly():
                    async for chunk in mdl.async_chat_streamly(
                        None,
                        [{"role": "user", "content": "Hi"}],
                        {"temperature": 0.9},
                    ):
                        if chunk and isinstance(chunk, str) and chunk.find("**ERROR**") < 0:
                            return True
                    return False

                result = await asyncio.wait_for(check_streamly(), timeout=timeout_seconds)
                if result:
                    chat_passed = True
                else:
                    raise Exception("No valid response received")
            except Exception as e:
                msg += f"\nFail to access model({llm.fid}/{llm.llm_name}) using this api key." + str(e)
        elif not rerank_passed and llm.model_type == LLMType.RERANK.value:
            assert factory in RerankModel, f"Re-rank model from {factory} is not supported yet."
            mdl = RerankModel[factory](req["api_key"], llm.llm_name, base_url=base_url)
            try:
                arr, tc = await asyncio.wait_for(
                    asyncio.to_thread(mdl.similarity, "What's the weather?", ["Is it sunny today?"]),
                    timeout=timeout_seconds,
                )
                if len(arr) == 0 or tc == 0:
                    raise Exception("Fail")
                rerank_passed = True
                logging.debug(f"passed model rerank {llm.llm_name}")
            except Exception as e:
                msg += f"\nFail to access model({llm.fid}/{llm.llm_name}) using this api key." + str(e)
        if any([embd_passed, chat_passed, rerank_passed]):
            msg = ""
            break

    if req.get("verify", False):
        return get_json_result(data={"message": msg, "success": len(msg.strip())==0})

    if msg:
        return get_data_error_result(message=msg)

    llm_config = {"api_key": req["api_key"], "api_base": base_url}
    for n in ["model_type", "llm_name"]:
        if n in req:
            llm_config[n] = req[n]

    for llm in source_llms:
        llm_config["max_tokens"] = llm.max_tokens
        if not TenantLLMService.filter_update([TenantLLM.tenant_id == current_user.id, TenantLLM.llm_factory == factory, TenantLLM.llm_name == llm.llm_name], llm_config):
            TenantLLMService.save(
                tenant_id=current_user.id,
                llm_factory=factory,
                llm_name=llm.llm_name,
                model_type=llm.model_type,
                api_key=llm_config["api_key"],
                api_base=llm_config["api_base"],
                max_tokens=llm_config["max_tokens"],
            )

    return get_json_result(data=True)