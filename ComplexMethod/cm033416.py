async def update_chat(chat_id):
    if not _ensure_owned_chat(chat_id):
        return get_json_result(
            data=False, message="No authorization.", code=RetCode.AUTHENTICATION_ERROR
        )

    try:
        req = await get_request_json()
        ok, tenant = TenantService.get_by_id(current_user.id)
        if not ok:
            return get_data_error_result(message="Tenant not found!")

        ok, current_chat = DialogService.get_by_id(chat_id)
        if not ok:
            return get_data_error_result(message="Chat not found!")
        current_chat = current_chat.to_dict()

        if req.get("tenant_id"):
            return get_data_error_result(message="`tenant_id` must not be provided.")

        if "name" in req:
            name, err = _validate_name(req.get("name"), required=True)
            if err:
                return get_data_error_result(message=err)
            req["name"] = name

        if "dataset_ids" in req:
            kb_ids = _validate_dataset_ids(req.get("dataset_ids"), current_user.id)
            if isinstance(kb_ids, str):
                return get_data_error_result(message=kb_ids)
            req["kb_ids"] = kb_ids
            req.pop("dataset_ids", None)

        if "llm_id" in req:
            err = _validate_llm_id(req.get("llm_id"), current_user.id, req.get("llm_setting"))
            if err:
                return get_data_error_result(message=err)

        if "rerank_id" in req:
            err = _validate_rerank_id(req.get("rerank_id"), current_user.id)
            if err:
                return get_data_error_result(message=err)

        if "prompt_config" in req:
            if not isinstance(req["prompt_config"], dict):
                return get_data_error_result(message="`prompt_config` should be an object.")
            # err = _validate_prompt_config(req["prompt_config"])
            # if err:
            #     return get_data_error_result(message=err)

        # prompt_config = req.get("prompt_config", {})
        # if not prompt_config:
        #     prompt_config = current_chat.get("prompt_config", {})
        # kb_ids = req.get("kb_ids", current_chat.get("kb_ids", []))
        # if not kb_ids and not prompt_config.get("tavily_api_key") and _has_knowledge_placeholder(prompt_config):
        #     return get_data_error_result(message="Please remove `{knowledge}` in system prompt since no dataset / Tavily used here.")

        req = ensure_tenant_model_id_for_params(current_user.id, req)
        req = {field: value for field, value in req.items() if field in _PERSISTED_FIELDS}
        for field in _READONLY_FIELDS:
            req.pop(field, None)

        if (
            "name" in req
            and req["name"].lower() != current_chat["name"].lower()
            and DialogService.query(
                name=req["name"],
                tenant_id=current_user.id,
                status=StatusEnum.VALID.value,
            )
        ):
            return get_data_error_result(message="Duplicated chat name.")

        if not DialogService.update_by_id(chat_id, req):
            return get_data_error_result(message="Chat not found!")

        ok, chat = DialogService.get_by_id(chat_id)
        if not ok:
            return get_data_error_result(message="Failed to retrieve updated chat.")
        return get_json_result(data=_build_chat_response(chat))
    except Exception as ex:
        return server_error_response(ex)