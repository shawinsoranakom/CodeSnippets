def apply_request_parameters(
    uri: str, integration: dict[str, Any], path_params: dict[str, str], query_params: dict[str, str]
):
    request_parameters = integration.get("requestParameters")
    uri = uri or integration.get("uri") or integration.get("integrationUri") or ""
    if request_parameters:
        for key in path_params:
            # check if path_params is present in the integration request parameters
            request_param_key = f"integration.request.path.{key}"
            request_param_value = f"method.request.path.{key}"
            if request_parameters.get(request_param_key) == request_param_value:
                uri = uri.replace(f"{{{key}}}", path_params[key])

    if integration.get("type") != "HTTP_PROXY" and request_parameters:
        for key in query_params.copy():
            request_query_key = f"integration.request.querystring.{key}"
            request_param_val = f"method.request.querystring.{key}"
            if request_parameters.get(request_query_key, None) != request_param_val:
                query_params.pop(key)

    return add_query_params_to_url(uri, query_params)