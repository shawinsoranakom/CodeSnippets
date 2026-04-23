def factories():
    try:
        fac = get_allowed_llm_factories()
        fac = [f.to_dict() for f in fac if f.name not in ["Youdao", "FastEmbed", "BAAI", "Builtin", "siliconflow_intl"]]
        llms = LLMService.get_all()
        mdl_types = {}
        for m in llms:
            if m.status != StatusEnum.VALID.value:
                continue
            if m.fid not in mdl_types:
                mdl_types[m.fid] = set([])
            mdl_types[m.fid].add(m.model_type)
        for f in fac:
            f["model_types"] = list(
                mdl_types.get(
                    f["name"],
                    [LLMType.CHAT, LLMType.EMBEDDING, LLMType.RERANK, LLMType.IMAGE2TEXT, LLMType.SPEECH2TEXT, LLMType.TTS, LLMType.OCR],
                )
            )

        return get_json_result(data=fac)
    except Exception as e:
        return server_error_response(e)