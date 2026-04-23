def get_model_config(cls, tenant_id, llm_type, llm_name=None):
        from api.db.services.llm_service import LLMService

        e, tenant = TenantService.get_by_id(tenant_id)
        if not e:
            raise LookupError("Tenant not found")

        if llm_type == LLMType.EMBEDDING.value:
            mdlnm = tenant.embd_id if not llm_name else llm_name
        elif llm_type == LLMType.SPEECH2TEXT.value:
            mdlnm = tenant.asr_id if not llm_name else llm_name
        elif llm_type == LLMType.IMAGE2TEXT.value:
            mdlnm = tenant.img2txt_id if not llm_name else llm_name
        elif llm_type == LLMType.CHAT.value:
            mdlnm = tenant.llm_id if not llm_name else llm_name
        elif llm_type == LLMType.RERANK:
            mdlnm = tenant.rerank_id if not llm_name else llm_name
        elif llm_type == LLMType.TTS:
            mdlnm = tenant.tts_id if not llm_name else llm_name
        elif llm_type == LLMType.OCR:
            if not llm_name:
                raise LookupError("OCR model name is required")
            mdlnm = llm_name
        else:
            assert False, "LLM type error"

        model_config = cls.get_api_key(tenant_id, mdlnm, llm_type)
        mdlnm, fid = TenantLLMService.split_model_name_and_factory(mdlnm)
        if not model_config:  # for some cases seems fid mismatch
            model_config = cls.get_api_key(tenant_id, mdlnm, llm_type)
        if model_config:
            model_config = model_config.to_dict()
        elif llm_type == LLMType.EMBEDDING and fid == "Builtin" and "tei-" in os.getenv("COMPOSE_PROFILES", "") and mdlnm == os.getenv("TEI_MODEL", ""):
            embedding_cfg = settings.EMBEDDING_CFG
            model_config = {"llm_factory": "Builtin", "api_key": embedding_cfg["api_key"], "llm_name": mdlnm, "api_base": embedding_cfg["base_url"]}
        else:
            raise LookupError(f"Model({mdlnm}@{fid}) not authorized")

        llm = LLMService.query(llm_name=mdlnm) if not fid else LLMService.query(llm_name=mdlnm, fid=fid)
        if not llm and fid:  # for some cases seems fid mismatch
            llm = LLMService.query(llm_name=mdlnm)
        if llm:
            model_config["is_tools"] = llm[0].is_tools
        return model_config