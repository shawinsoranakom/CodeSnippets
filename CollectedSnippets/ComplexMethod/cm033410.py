async def update(search_id):
    req = await get_request_json()
    if not isinstance(req["name"], str):
        return get_data_error_result(message="Search name must be string.")
    if req["name"].strip() == "":
        return get_data_error_result(message="Search name can't be empty.")
    if len(req["name"].encode("utf-8")) > DATASET_NAME_LIMIT:
        return get_data_error_result(message=f"Search name length is {len(req['name'])} which is large than {DATASET_NAME_LIMIT}")
    req["name"] = req["name"].strip()

    e, _ = TenantService.get_by_id(current_user.id)
    if not e:
        return get_data_error_result(message="Authorized identity.")

    if not SearchService.accessible4deletion(search_id, current_user.id):
        return get_json_result(data=False, message="No authorization.", code=RetCode.AUTHENTICATION_ERROR)

    try:
        search_app = SearchService.query(tenant_id=current_user.id, id=search_id)[0]
        if not search_app:
            return get_json_result(data=False, message=f"Cannot find search {search_id}", code=RetCode.DATA_ERROR)

        if req["name"].lower() != search_app.name.lower() and len(SearchService.query(name=req["name"], tenant_id=current_user.id, status=StatusEnum.VALID.value)) >= 1:
            return get_data_error_result(message="Duplicated search name.")

        current_config = search_app.search_config or {}
        new_config = req["search_config"]
        if not isinstance(new_config, dict):
            return get_data_error_result(message="search_config must be a JSON object")
        req["search_config"] = {**current_config, **new_config}

        for field in ("search_id", "tenant_id", "created_by", "update_time", "id"):
            req.pop(field, None)

        updated = SearchService.update_by_id(search_id, req)
        if not updated:
            return get_data_error_result(message="Failed to update search")

        e, updated_search = SearchService.get_by_id(search_id)
        if not e:
            return get_data_error_result(message="Failed to fetch updated search")

        return get_json_result(data=updated_search.to_dict())

    except Exception as e:
        return server_error_response(e)