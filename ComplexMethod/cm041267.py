def connect_api_gateway_to_http_with_lambda_proxy(
    gateway_name,
    target_uri,
    stage_name=None,
    methods=None,
    path=None,
    auth_type=None,
    auth_creator_func=None,
    http_method=None,
    client=None,
    role_arn: str = None,
):
    if methods is None:
        methods = []
    if not methods:
        methods = ["GET", "POST", "DELETE"]
    if not path:
        path = "/"
    stage_name = stage_name or "test"
    resources = {}
    resource_path = path.lstrip("/")
    resources[resource_path] = []

    for method in methods:
        int_meth = http_method or method
        integration = {"type": "AWS_PROXY", "uri": target_uri, "httpMethod": int_meth}
        if role_arn:
            integration["credentials"] = role_arn
        resources[resource_path].append(
            {
                "httpMethod": method,
                "authorizationType": auth_type,
                "authorizerId": None,
                "integrationHttpMethod": "POST",
                "integrations": [integration],
            }
        )
    return resource_utils.create_api_gateway(
        name=gateway_name,
        resources=resources,
        stage_name=stage_name,
        auth_creator_func=auth_creator_func,
        client=client,
    )