async def detail_share_embedded():
    token = request.headers.get("Authorization").split()
    if len(token) != 2:
        return get_error_data_result(message='Authorization is not valid!')
    token = token[1]
    objs = APIToken.query(beta=token)
    if not objs:
        return get_error_data_result(message='Authentication error: API key is invalid!"')

    search_id = request.args["search_id"]
    tenant_id = objs[0].tenant_id
    if not tenant_id:
        return get_error_data_result(message="permission denined.")
    try:
        tenants = UserTenantService.query(user_id=tenant_id)
        for tenant in tenants:
            if SearchService.query(tenant_id=tenant.tenant_id, id=search_id):
                break
        else:
            return get_json_result(data=False, message="Has no permission for this operation.",
                                   code=RetCode.OPERATING_ERROR)

        search = SearchService.get_detail(search_id)
        if not search:
            return get_error_data_result(message="Can't find this Search App!")
        return get_json_result(data=search)
    except Exception as e:
        return server_error_response(e)