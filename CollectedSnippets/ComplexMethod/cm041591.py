def create_api_gateway_and_deploy(
        apigw_client,
        dynamodb_client,
        request_templates=None,
        response_templates=None,
        is_api_key_required=False,
        integration_type=None,
        integration_responses=None,
        stage_name="staging",
        role_arn: str = None,
    ):
        response_templates = response_templates or {}
        request_templates = request_templates or {}
        integration_type = integration_type or "AWS"
        response = apigw_client.create_rest_api(name="my_api", description="this is my api")
        api_id = response["id"]
        resources = apigw_client.get_resources(restApiId=api_id)
        root_resources = [resource for resource in resources["items"] if resource["path"] == "/"]
        root_id = root_resources[0]["id"]

        kwargs = {}
        if integration_type == "AWS":
            resource_util.create_dynamodb_table(
                "MusicCollection", partition_key="id", client=dynamodb_client
            )
            kwargs["uri"] = (
                f"arn:aws:apigateway:{apigw_client.meta.region_name}:dynamodb:action/PutItem&Table=MusicCollection"
            )

        if role_arn:
            kwargs["credentials"] = role_arn

        if not integration_responses:
            integration_responses = [{"httpMethod": "PUT", "statusCode": "200"}]

        for resp_details in integration_responses:
            apigw_client.put_method(
                restApiId=api_id,
                resourceId=root_id,
                httpMethod=resp_details["httpMethod"],
                authorizationType="NONE",
                apiKeyRequired=is_api_key_required,
            )

            apigw_client.put_method_response(
                restApiId=api_id,
                resourceId=root_id,
                httpMethod=resp_details["httpMethod"],
                statusCode="200",
            )

            apigw_client.put_integration(
                restApiId=api_id,
                resourceId=root_id,
                httpMethod=resp_details["httpMethod"],
                integrationHttpMethod=resp_details["httpMethod"],
                type=integration_type,
                requestTemplates=request_templates,
                **kwargs,
            )

            apigw_client.put_integration_response(
                restApiId=api_id,
                resourceId=root_id,
                selectionPattern="",
                responseTemplates=response_templates,
                **resp_details,
            )

        apigw_client.create_deployment(restApiId=api_id, stageName=stage_name)
        return api_id