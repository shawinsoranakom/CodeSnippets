async def create():
    try:
        req = await get_request_json()
        ok, tenant = TenantService.get_by_id(current_user.id)
        if not ok:
            return get_data_error_result(message="Tenant not found!")

        # Validate tenant_id should not be provided
        if req.get("tenant_id"):
            return get_data_error_result(message="`tenant_id` must not be provided.")

        # Validate name
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

        req.setdefault("kb_ids", [])
        req.setdefault("llm_id", tenant.llm_id)
        if req["llm_id"] is None:
            req["llm_id"] = tenant.llm_id
        req.setdefault("llm_setting", {})
        req.setdefault("description", "A helpful Assistant")
        req.setdefault("top_n", 6)
        req.setdefault("top_k", 1024)
        req.setdefault("rerank_id", "")
        req.setdefault("similarity_threshold", 0.1)
        req.setdefault("vector_similarity_weight", 0.3)
        req.setdefault("icon", "")
        _apply_prompt_defaults(req)
        # err = _validate_prompt_config(req["prompt_config"])
        # if err:
        #     return get_data_error_result(message=err)

        req = ensure_tenant_model_id_for_params(current_user.id, req)
        req = {field: value for field, value in req.items() if field in _PERSISTED_FIELDS}
        for field in _READONLY_FIELDS:
            req.pop(field, None)

        if DialogService.query(
            name=req["name"],
            tenant_id=current_user.id,
            status=StatusEnum.VALID.value,
        ):
            return get_data_error_result(message="Duplicated chat name in creating chat.")

        req["id"] = get_uuid()
        req["tenant_id"] = current_user.id
        if not DialogService.save(**req):
            return get_data_error_result(message="Failed to create chat.")

        ok, chat = DialogService.get_by_id(req["id"])
        if not ok:
            return get_data_error_result(message="Failed to retrieve created chat.")
        return get_json_result(data=_build_chat_response(chat))
    except Exception as ex:
        return server_error_response(ex)