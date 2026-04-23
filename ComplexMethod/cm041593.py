def _factory(
        integration_uri,
        path_part="test",
        req_parameters=None,
        req_templates=None,
        res_templates=None,
        integration_type=None,
        stage=DEFAULT_STAGE_NAME,
        resource_method: str = "POST",
        integration_method: str = "POST",
    ):
        name = f"test-apigw-{short_uid()}"
        api_id, name, root_id = create_rest_apigw(
            name=name, endpointConfiguration={"types": ["REGIONAL"]}
        )

        resource_id, _ = create_rest_resource(
            aws_client.apigateway, restApiId=api_id, parentId=root_id, pathPart=path_part
        )

        if req_parameters is None:
            req_parameters = {}

        method, _ = create_rest_resource_method(
            aws_client.apigateway,
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=resource_method,
            authorizationType="NONE",
            apiKeyRequired=False,
            requestParameters=dict.fromkeys(req_parameters.values(), True),
        )

        # set AWS policy to give API GW access to backend resources
        if ":dynamodb:" in integration_uri:
            policy = APIGATEWAY_DYNAMODB_POLICY
        elif ":kinesis:" in integration_uri:
            policy = APIGATEWAY_KINESIS_POLICY
        elif integration_type in ("HTTP", "HTTP_PROXY"):
            policy = None
        else:
            raise Exception(f"Unexpected integration URI: {integration_uri}")
        assume_role_arn = ""
        if policy:
            assume_role_arn = create_iam_role_with_policy(
                RoleName=f"role-apigw-{short_uid()}",
                PolicyName=f"policy-apigw-{short_uid()}",
                RoleDefinition=APIGATEWAY_ASSUME_ROLE_POLICY,
                PolicyDefinition=policy,
            )

        create_rest_api_integration(
            aws_client.apigateway,
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=method,
            integrationHttpMethod=integration_method,
            type=integration_type or "AWS",
            credentials=assume_role_arn,
            uri=integration_uri,
            requestTemplates=req_templates or {},
            requestParameters=req_parameters,
        )

        create_rest_api_method_response(
            aws_client.apigateway,
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=resource_method,
            statusCode="200",
        )

        res_templates = res_templates or {APPLICATION_JSON: "$input.json('$')"}
        create_rest_api_integration_response(
            aws_client.apigateway,
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod=resource_method,
            statusCode="200",
            responseTemplates=res_templates,
        )

        deployment_id, _ = create_rest_api_deployment(aws_client.apigateway, restApiId=api_id)
        create_rest_api_stage(
            aws_client.apigateway, restApiId=api_id, stageName=stage, deploymentId=deployment_id
        )

        return api_id