def get_event_request_context(invocation_context: ApiInvocationContext):
    method = invocation_context.method
    path = invocation_context.path
    headers = invocation_context.headers
    integration_uri = invocation_context.integration_uri
    resource_path = invocation_context.resource_path
    resource_id = invocation_context.resource_id

    set_api_id_stage_invocation_path(invocation_context)
    api_id = invocation_context.api_id
    stage = invocation_context.stage

    if "_user_request_" in invocation_context.raw_uri:
        full_path = invocation_context.raw_uri.partition("_user_request_")[2]
    else:
        full_path = invocation_context.raw_uri.removeprefix(f"/{stage}")
    relative_path, query_string_params = extract_query_string_params(path=full_path)

    source_ip = invocation_context.auth_identity.get("sourceIp")
    integration_uri = integration_uri or ""
    account_id = integration_uri.split(":lambda:path")[-1].split(":function:")[0].split(":")[-1]
    account_id = account_id or DEFAULT_AWS_ACCOUNT_ID
    request_context = {
        "accountId": account_id,
        "apiId": api_id,
        "resourcePath": resource_path or relative_path,
        "domainPrefix": invocation_context.domain_prefix,
        "domainName": invocation_context.domain_name,
        "resourceId": resource_id,
        "requestId": long_uid(),
        "identity": {
            "accountId": account_id,
            "sourceIp": source_ip,
            "userAgent": headers.get("User-Agent"),
        },
        "httpMethod": method,
        "protocol": "HTTP/1.1",
        "requestTime": datetime.now(UTC).strftime(REQUEST_TIME_DATE_FORMAT),
        "requestTimeEpoch": int(time.time() * 1000),
        "authorizer": {},
    }

    if invocation_context.is_websocket_request():
        request_context["connectionId"] = invocation_context.connection_id

    # set "authorizer" and "identity" event attributes from request context
    authorizer_result = invocation_context.authorizer_result
    if authorizer_result:
        request_context["authorizer"] = authorizer_result
    request_context["identity"].update(invocation_context.auth_identity or {})

    if not is_test_invoke_method(method, path):
        request_context["path"] = (f"/{stage}" if stage else "") + relative_path
        request_context["stage"] = stage
    return request_context