def get_api_key(cls, tenant_id, model_name, model_type=None):
        mdlnm, fid = TenantLLMService.split_model_name_and_factory(model_name)
        model_type_val = model_type.value if hasattr(model_type, "value") else model_type
        query_kwargs = {"tenant_id": tenant_id, "llm_name": mdlnm}
        if model_type_val is not None:
            query_kwargs["model_type"] = model_type_val
        if not fid:
            objs = cls.query(**query_kwargs)
        else:
            objs = cls.query(**query_kwargs, llm_factory=fid)

        if (not objs) and fid:
            if fid == "LocalAI":
                mdlnm += "___LocalAI"
            elif fid == "HuggingFace":
                mdlnm += "___HuggingFace"
            elif fid == "OpenAI-API-Compatible":
                mdlnm += "___OpenAI-API"
            elif fid == "VLLM":
                mdlnm += "___VLLM"
            query_kwargs["llm_name"] = mdlnm
            objs = cls.query(**query_kwargs, llm_factory=fid)
        if not objs:
            return None
        return objs[0]