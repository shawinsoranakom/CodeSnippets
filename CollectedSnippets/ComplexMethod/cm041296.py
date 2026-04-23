def create_api_gateway_integrations(api_id, resource_id, method, integrations=None, client=None):
    if integrations is None:
        integrations = []
    if not client:
        client = connect_to().apigateway
    for integration in integrations:
        req_templates = integration.get("requestTemplates") or {}
        res_templates = integration.get("responseTemplates") or {}
        success_code = integration.get("successCode") or "200"
        client_error_code = integration.get("clientErrorCode") or "400"
        server_error_code = integration.get("serverErrorCode") or "500"
        request_parameters = integration.get("requestParameters") or {}
        credentials = integration.get("credentials") or ""

        # create integration
        client.put_integration(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=method["httpMethod"],
            integrationHttpMethod=method.get("integrationHttpMethod") or method["httpMethod"],
            type=integration["type"],
            uri=integration["uri"],
            requestTemplates=req_templates,
            requestParameters=request_parameters,
            credentials=credentials,
        )
        response_configs = [
            {"pattern": "^2.*", "code": success_code, "res_templates": res_templates},
            {"pattern": "^4.*", "code": client_error_code, "res_templates": {}},
            {"pattern": "^5.*", "code": server_error_code, "res_templates": {}},
        ]
        # create response configs
        for response_config in response_configs:
            # create integration response
            client.put_integration_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=method["httpMethod"],
                statusCode=response_config["code"],
                responseTemplates=response_config["res_templates"],
                selectionPattern=response_config["pattern"],
            )
            # create method response
            client.put_method_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=method["httpMethod"],
                statusCode=response_config["code"],
            )