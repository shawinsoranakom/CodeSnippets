def invoke_rest_api(invocation_context: ApiInvocationContext):
    invocation_path = invocation_context.path_with_query_string
    raw_path = invocation_context.path or invocation_path
    method = invocation_context.method
    headers = invocation_context.headers

    extracted_path, resource = get_target_resource_details(invocation_context)
    if not resource:
        return make_error_response(f"Unable to find path {invocation_context.path}", 404)

    # validate request
    validator = RequestValidator(invocation_context)
    try:
        validator.validate_request()
    except (BadRequestParameters, BadRequestBody) as e:
        return e.to_response()

    api_key_required = resource.get("resourceMethods", {}).get(method, {}).get("apiKeyRequired")
    if api_key_required and not is_api_key_valid(invocation_context):
        raise AuthorizationError("Forbidden", 403)

    resource_methods = resource.get("resourceMethods", {})
    resource_method = resource_methods.get(method, {})
    if not resource_method:
        # HttpMethod: '*'
        # ResourcePath: '/*' - produces 'X-AMAZON-APIGATEWAY-ANY-METHOD'
        resource_method = resource_methods.get("ANY", {}) or resource_methods.get(
            "X-AMAZON-APIGATEWAY-ANY-METHOD", {}
        )
    method_integration = resource_method.get("methodIntegration")
    if not method_integration:
        if method == "OPTIONS" and "Origin" in headers:
            # default to returning CORS headers if this is an OPTIONS request
            return get_cors_response(headers)
        return make_error_response(
            f"Unable to find integration for: {method} {invocation_path} ({raw_path})",
            404,
        )

    # update fields in invocation context, then forward request to next handler
    invocation_context.resource_path = extracted_path
    invocation_context.integration = method_integration

    return invoke_rest_api_integration(invocation_context)