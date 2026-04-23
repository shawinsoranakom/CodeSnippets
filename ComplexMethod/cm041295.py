def create_api_gateway(
    name,
    description=None,
    resources=None,
    stage_name=None,
    enabled_api_keys=None,
    usage_plan_name=None,
    auth_creator_func=None,  # function that receives an api_id and returns an authorizer_id
    client=None,
):
    if enabled_api_keys is None:
        enabled_api_keys = []
    if not client:
        client = connect_to().apigateway
    resources = resources or []
    stage_name = stage_name or "testing"
    usage_plan_name = usage_plan_name or "Basic Usage"
    description = description or f'Test description for API "{name}"'

    LOG.info('Creating API resources under API Gateway "%s".', name)
    api = client.create_rest_api(name=name, description=description)
    api_id = api["id"]

    auth_id = None
    if auth_creator_func:
        auth_id = auth_creator_func(api_id)

    resources_list = client.get_resources(restApiId=api_id)
    root_res_id = resources_list["items"][0]["id"]
    # add API resources and methods
    for path, methods in resources.items():
        # create resources recursively
        parent_id = root_res_id
        for path_part in path.split("/"):
            api_resource = client.create_resource(
                restApiId=api_id, parentId=parent_id, pathPart=path_part
            )
            parent_id = api_resource["id"]
        # add methods to the API resource
        for method in methods:
            kwargs = {"authorizerId": auth_id} if auth_id else {}
            client.put_method(
                restApiId=api_id,
                resourceId=api_resource["id"],
                httpMethod=method["httpMethod"],
                authorizationType=method.get("authorizationType") or "NONE",
                apiKeyRequired=method.get("apiKeyRequired") or False,
                requestParameters=method.get("requestParameters") or {},
                requestModels=method.get("requestModels") or {},
                **kwargs,
            )
            # create integrations for this API resource/method
            integrations = method["integrations"]
            create_api_gateway_integrations(
                api_id,
                api_resource["id"],
                method,
                integrations,
                client=client,
            )

    # deploy the API gateway
    client.create_deployment(restApiId=api_id, stageName=stage_name)
    return api