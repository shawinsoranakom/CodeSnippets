def set_api_id_stage_invocation_path(
    invocation_context: ApiInvocationContext,
) -> ApiInvocationContext:
    # skip if all details are already available
    values = (
        invocation_context.api_id,
        invocation_context.stage,
        invocation_context.path_with_query_string,
    )
    if all(values):
        return invocation_context

    # skip if this is a websocket request
    if invocation_context.is_websocket_request():
        return invocation_context

    path = invocation_context.path
    headers = invocation_context.headers

    path_match = re.search(PATH_REGEX_USER_REQUEST, path)
    host_header = headers.get(HEADER_LOCALSTACK_EDGE_URL, "") or headers.get("Host") or ""
    host_match = re.search(HOST_REGEX_EXECUTE_API, host_header)
    test_invoke_match = re.search(PATH_REGEX_TEST_INVOKE_API, path)
    if path_match:
        api_id = path_match.group(1)
        stage = path_match.group(2)
        relative_path_w_query_params = f"/{path_match.group(3)}"
    elif host_match:
        api_id = extract_api_id_from_hostname_in_url(host_header)
        stage = path.strip("/").split("/")[0]
        relative_path_w_query_params = "/{}".format(path.lstrip("/").partition("/")[2])
    elif test_invoke_match:
        stage = invocation_context.stage
        api_id = invocation_context.api_id
        relative_path_w_query_params = invocation_context.path_with_query_string
    else:
        raise Exception(
            f"Unable to extract API Gateway details from request: {path} {dict(headers)}"
        )

    # set details in invocation context
    invocation_context.api_id = api_id
    invocation_context.stage = stage
    invocation_context.path_with_query_string = relative_path_w_query_params
    return invocation_context