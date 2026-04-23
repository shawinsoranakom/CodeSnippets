async def add_llm():
    req = await get_request_json()
    factory = req["llm_factory"]
    api_key = req.get("api_key", "x")
    llm_name = req.get("llm_name")
    timeout_seconds = int(os.environ.get("LLM_TIMEOUT_SECONDS", 10))

    if factory not in [f.name for f in get_allowed_llm_factories()]:
        return get_data_error_result(message=f"LLM factory {factory} is not allowed")

    def apikey_json(keys):
        nonlocal req
        return json.dumps({k: req.get(k, "") for k in keys})

    if factory == "VolcEngine":
        # For VolcEngine, due to its special authentication method
        # Assemble ark_api_key endpoint_id into api_key
        api_key = apikey_json(["ark_api_key", "endpoint_id"])

    elif factory == "Tencent Cloud":
        req["api_key"] = apikey_json(["tencent_cloud_sid", "tencent_cloud_sk"])
        return await set_api_key()

    elif factory == "Bedrock":
        # For Bedrock, due to its special authentication method
        # Assemble bedrock_ak, bedrock_sk, bedrock_region
        api_key = apikey_json(["auth_mode", "bedrock_ak", "bedrock_sk", "bedrock_region", "aws_role_arn"])

    elif factory == "LocalAI":
        llm_name += "___LocalAI"

    elif factory == "HuggingFace":
        llm_name += "___HuggingFace"

    elif factory == "OpenAI-API-Compatible":
        llm_name += "___OpenAI-API"

    elif factory == "VLLM":
        llm_name += "___VLLM"

    elif factory == "XunFei Spark":
        if req["model_type"] == "chat":
            api_key = req.get("spark_api_password", "")
        elif req["model_type"] == "tts":
            api_key = apikey_json(["spark_app_id", "spark_api_secret", "spark_api_key"])

    elif factory == "BaiduYiyan":
        api_key = apikey_json(["yiyan_ak", "yiyan_sk"])

    elif factory == "Fish Audio":
        api_key = apikey_json(["fish_audio_ak", "fish_audio_refid"])

    elif factory == "Google Cloud":
        api_key = apikey_json(["google_project_id", "google_region", "google_service_account_key"])

    elif factory == "Azure-OpenAI":
        api_key = apikey_json(["api_key", "api_version"])

    elif factory == "OpenRouter":
        api_key = apikey_json(["api_key", "provider_order"])

    elif factory == "MinerU":
        api_key = apikey_json(["api_key", "provider_order"])

    elif factory == "PaddleOCR":
        api_key = apikey_json(["api_key", "provider_order"])

    llm = {
        "tenant_id": current_user.id,
        "llm_factory": factory,
        "model_type": req["model_type"],
        "llm_name": llm_name,
        "api_base": req.get("api_base", ""),
        "api_key": api_key,
        "max_tokens": req.get("max_tokens"),
    }

    msg = ""
    mdl_nm = llm["llm_name"].split("___")[0]
    extra = {"provider": factory}
    model_type = llm["model_type"]
    model_api_key = llm["api_key"]
    model_base_url = llm.get("api_base", "")
    match model_type:
        case LLMType.EMBEDDING.value:
            assert factory in EmbeddingModel, f"Embedding model from {factory} is not supported yet."
            mdl = EmbeddingModel[factory](key=model_api_key, model_name=mdl_nm, base_url=model_base_url)
            try:
                arr, tc = await asyncio.wait_for(
                    asyncio.to_thread(mdl.encode, ["Test if the api key is available"]),
                    timeout=timeout_seconds,
                )
                if len(arr[0]) == 0:
                    raise Exception("Fail")
            except Exception as e:
                msg += f"\nFail to access embedding model({mdl_nm})." + str(e)
        case LLMType.CHAT.value:
            assert factory in ChatModel, f"Chat model from {factory} is not supported yet."
            mdl = ChatModel[factory](
                key=model_api_key,
                model_name=mdl_nm,
                base_url=model_base_url,
                **extra,
            )
            try:
                async def check_streamly():
                    async for chunk in mdl.async_chat_streamly(
                        None,
                        [{"role": "user", "content": "Hi"}],
                        {"temperature": 0.9},
                    ):
                        if chunk and isinstance(chunk, str) and chunk.find("**ERROR**:") < 0:
                            return True
                    return False

                result = await asyncio.wait_for(check_streamly(), timeout=timeout_seconds)
                if not result:
                    raise Exception("No valid response received")
            except Exception as e:
                msg += f"\nFail to access model({factory}/{mdl_nm})." + str(e)

        case LLMType.RERANK.value:
            assert factory in RerankModel, f"RE-rank model from {factory} is not supported yet."
            try:
                mdl = RerankModel[factory](key=model_api_key, model_name=mdl_nm, base_url=model_base_url)
                arr, tc = await asyncio.wait_for(
                    asyncio.to_thread(mdl.similarity, "Hello~ RAGFlower!", ["Hi, there!", "Ohh, my friend!"]),
                    timeout=timeout_seconds,
                )
                if len(arr) == 0:
                    raise Exception("Not known.")
            except KeyError:
                msg += f"{factory} dose not support this model({factory}/{mdl_nm})"
            except Exception as e:
                msg += f"\nFail to access model({factory}/{mdl_nm})." + str(e)

        case LLMType.IMAGE2TEXT.value:
            assert factory in CvModel, f"Image to text model from {factory} is not supported yet."
            mdl = CvModel[factory](key=model_api_key, model_name=mdl_nm, base_url=model_base_url)
            try:
                image_data = test_image
                m, tc = await asyncio.wait_for(
                    asyncio.to_thread(mdl.describe, image_data),
                    timeout=timeout_seconds,
                )
                if not tc and m.find("**ERROR**:") >= 0:
                    raise Exception(m)
            except Exception as e:
                msg += f"\nFail to access model({factory}/{mdl_nm})." + str(e)
        case LLMType.TTS.value:
            assert factory in TTSModel, f"TTS model from {factory} is not supported yet."
            mdl = TTSModel[factory](key=model_api_key, model_name=mdl_nm, base_url=model_base_url)
            try:
                def drain_tts():
                    for _ in mdl.tts("Hello~ RAGFlower!"):
                        pass

                await asyncio.wait_for(
                    asyncio.to_thread(drain_tts),
                    timeout=timeout_seconds,
                )
            except RuntimeError as e:
                msg += f"\nFail to access model({factory}/{mdl_nm})." + str(e)
        case LLMType.OCR.value:
            assert factory in OcrModel, f"OCR model from {factory} is not supported yet."
            try:
                mdl = OcrModel[factory](key=model_api_key, model_name=mdl_nm, base_url=model_base_url)
                ok, reason = await asyncio.wait_for(
                    asyncio.to_thread(mdl.check_available),
                    timeout=timeout_seconds,
                )
                if not ok:
                    raise RuntimeError(reason or "Model not available")
            except Exception as e:
                msg += f"\nFail to access model({factory}/{mdl_nm})." + str(e)
        case LLMType.SPEECH2TEXT.value:
            assert factory in Seq2txtModel, f"Speech model from {factory} is not supported yet."
            try:
                mdl = Seq2txtModel[factory](key=model_api_key, model_name=mdl_nm, base_url=model_base_url)
                # TODO: check the availability
            except Exception as e:
                msg += f"\nFail to access model({factory}/{mdl_nm})." + str(e)
        case _:
            raise RuntimeError(f"Unknown model type: {model_type}")

    if req.get("verify", False):
        return get_json_result(data={"message": msg, "success": len(msg.strip()) == 0})

    if msg:
        return get_data_error_result(message=msg)

    if not TenantLLMService.filter_update([TenantLLM.tenant_id == current_user.id, TenantLLM.llm_factory == factory, TenantLLM.llm_name == llm["llm_name"]], llm):
        TenantLLMService.save(**llm)

    return get_json_result(data=True)