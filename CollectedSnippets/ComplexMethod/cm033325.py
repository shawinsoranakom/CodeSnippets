async def list_app():
    self_deployed = ["FastEmbed", "Ollama", "Xinference", "LocalAI", "LM-Studio", "GPUStack"]
    weighted = []
    model_type = request.args.get("model_type")
    tenant_id = current_user.id
    try:
        TenantLLMService.ensure_mineru_from_env(tenant_id)
        objs = TenantLLMService.query(tenant_id=tenant_id)
        facts = set([o.to_dict()["llm_factory"] for o in objs if o.api_key and o.status == StatusEnum.VALID.value])
        tenant_llm_mapping = {f"{o.llm_name}@{o.llm_factory}": o for o in objs}
        status = {(o.llm_name + "@" + o.llm_factory) for o in objs if o.status == StatusEnum.VALID.value}
        llms = LLMService.get_all()
        llms = [m.to_dict() for m in llms if m.status == StatusEnum.VALID.value and m.fid not in weighted and (m.fid == "Builtin" or (m.llm_name + "@" + m.fid) in status)]
        for m in llms:
            m["id"] = tenant_llm_mapping.get(m["llm_name"] + "@" + m["fid"], TenantLLM(id=None)).id
            m["available"] = m["fid"] in facts or m["llm_name"].lower() == "flag-embedding" or m["fid"] in self_deployed
            if "tei-" in os.getenv("COMPOSE_PROFILES", "") and m["model_type"] == LLMType.EMBEDDING and m["fid"] == "Builtin" and m["llm_name"] == os.getenv("TEI_MODEL", ""):
                m["available"] = True

        llm_set = set([m["llm_name"] + "@" + m["fid"] for m in llms])
        for o in objs:
            if o.llm_name + "@" + o.llm_factory in llm_set:
                continue
            llms.append({"id": o.id, "llm_name": o.llm_name, "model_type": o.model_type, "fid": o.llm_factory, "available": True, "status": StatusEnum.VALID.value})

        res = {}
        for m in llms:
            if model_type and m["model_type"].find(model_type) < 0:
                continue
            if m["fid"] not in res:
                res[m["fid"]] = []
            res[m["fid"]].append(m)

        return get_json_result(data=res)
    except Exception as e:
        return server_error_response(e)