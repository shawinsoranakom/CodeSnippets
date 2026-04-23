def my_llms():
    try:
        TenantLLMService.ensure_mineru_from_env(current_user.id)
        include_details = request.args.get("include_details", "false").lower() == "true"

        if include_details:
            res = {}
            objs = TenantLLMService.query(tenant_id=current_user.id)
            factories = LLMFactoriesService.query(status=StatusEnum.VALID.value)

            for o in objs:
                o_dict = o.to_dict()
                factory_tags = None
                for f in factories:
                    if f.name == o_dict["llm_factory"]:
                        factory_tags = f.tags
                        break

                if o_dict["llm_factory"] not in res:
                    res[o_dict["llm_factory"]] = {"tags": factory_tags, "llm": []}

                res[o_dict["llm_factory"]]["llm"].append(
                    {
                        "id": o_dict["id"],
                        "type": o_dict["model_type"],
                        "name": o_dict["llm_name"],
                        "used_token": o_dict["used_tokens"],
                        "api_base": o_dict["api_base"] or "",
                        "max_tokens": o_dict["max_tokens"] or 8192,
                        "status": o_dict["status"] or "1",
                    }
                )
        else:
            res = {}
            for o in TenantLLMService.get_my_llms(current_user.id):
                if o["llm_factory"] not in res:
                    res[o["llm_factory"]] = {"tags": o["tags"], "llm": []}
                res[o["llm_factory"]]["llm"].append({"id": o["id"], "type": o["model_type"], "name": o["llm_name"], "used_token": o["used_tokens"], "status": o["status"]})

        return get_json_result(data=res)
    except Exception as e:
        return server_error_response(e)