def test_lambda_aws_proxy_response_format(
    create_rest_apigw, create_lambda_function, create_role_with_policy, aws_client
):
    stage_name = "test"
    _, role_arn = create_role_with_policy(
        "Allow", "lambda:InvokeFunction", json.dumps(APIGATEWAY_ASSUME_ROLE_POLICY), "*"
    )

    # create 2 lambdas
    function_name = f"test-function-{short_uid()}"
    create_function_response = create_lambda_function(
        func_name=function_name,
        handler_file=TEST_LAMBDA_AWS_PROXY_FORMAT,
        handler="lambda_aws_proxy_format.handler",
        runtime=Runtime.python3_12,
    )
    # create invocation role
    lambda_arn = create_function_response["CreateFunctionResponse"]["FunctionArn"]

    # create rest api
    api_id, _, root = create_rest_apigw(
        name=f"test-api-{short_uid()}",
        description="Integration test API",
    )

    resource_id = aws_client.apigateway.create_resource(
        restApiId=api_id, parentId=root, pathPart="{proxy+}"
    )["id"]

    aws_client.apigateway.put_method(
        restApiId=api_id,
        resourceId=resource_id,
        httpMethod="ANY",
        authorizationType="NONE",
    )

    # Lambda AWS_PROXY integration
    aws_client.apigateway.put_integration(
        restApiId=api_id,
        resourceId=resource_id,
        httpMethod="ANY",
        type="AWS_PROXY",
        integrationHttpMethod="POST",
        uri=f"arn:aws:apigateway:{aws_client.apigateway.meta.region_name}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations",
        credentials=role_arn,
    )

    aws_client.apigateway.create_deployment(restApiId=api_id, stageName=stage_name)

    format_types = [
        "no-body",
        "only-headers",
        "wrong-format",
        "empty-response",
    ]
    # TODO: refactor the test to use a lambda that returns whatever we pass it to instead of pre-defined responses
    for lambda_format_type in format_types:
        # invoke rest api
        invocation_url = api_invoke_url(
            api_id=api_id,
            stage=stage_name,
            path=f"/{lambda_format_type}",
        )

        def invoke_api(url):
            # use test header with different casing to check if it is preserved in the proxy payload
            response = requests.get(
                url,
                headers={"User-Agent": "python-requests/testing"},
                verify=False,
            )
            if lambda_format_type == "wrong-format":
                assert response.status_code == 502
            else:
                assert response.status_code == 200
            return response

        # retry is necessary against AWS, probably IAM permission delay
        response = retry(invoke_api, sleep=2, retries=10, url=invocation_url)

        if lambda_format_type in ("no-body", "only-headers", "empty-response"):
            assert response.content == b""
            if lambda_format_type == "only-headers":
                assert response.headers["test-header"] == "value"

        elif lambda_format_type == "wrong-format":
            assert response.status_code == 502
            assert response.json() == {"message": "Internal server error"}