def test_aws_proxy_binary_response(
    create_rest_apigw,
    create_lambda_function,
    create_role_with_policy,
    aws_client,
    region_name,
):
    _, role_arn = create_role_with_policy(
        "Allow", "lambda:InvokeFunction", json.dumps(APIGATEWAY_ASSUME_ROLE_POLICY), "*"
    )
    timeout = 30 if is_aws_cloud() else 3

    function_name = f"response-format-apigw-{short_uid()}"
    create_function_response = create_lambda_function(
        handler_file=LAMBDA_RESPONSE_FROM_BODY,
        func_name=function_name,
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
        uri=f"arn:aws:apigateway:{region_name}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations",
        credentials=role_arn,
    )

    # this deployment does not have any `binaryMediaTypes` configured, so it should not return any binary data
    stage_1 = "test"
    aws_client.apigateway.create_deployment(restApiId=api_id, stageName=stage_1)
    endpoint = api_invoke_url(api_id=api_id, path="/test", stage=stage_1)
    # Base64-encoded PNG image (example: 1x1 pixel transparent PNG)
    image_base64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR42mP8/wIAAgkBAyMAlYwAAAAASUVORK5CYII="
    binary_data = base64.b64decode(image_base64)

    decoded_response = {
        "statusCode": 200,
        "body": image_base64,
        "isBase64Encoded": True,
        "headers": {
            "Content-Type": "image/png",
            "Cache-Control": "no-cache",
        },
    }

    def _assert_invoke(accept: str | None, expect_binary: bool) -> bool:
        headers = {"User-Agent": "python/test"}
        if accept:
            headers["Accept"] = accept

        _response = requests.post(
            url=endpoint,
            data=json.dumps(decoded_response),
            headers=headers,
        )
        if not _response.status_code == 200:
            return False

        if expect_binary:
            return _response.content == binary_data
        else:
            return _response.text == image_base64

    # we poll that the API is returning the right data after deployment
    poll_condition(
        lambda: _assert_invoke(accept="image/png", expect_binary=False), timeout=timeout, interval=1
    )
    if is_aws_cloud():
        time.sleep(5)

    # we did not configure binaryMedias so the API is not returning binary data even if all conditions are met
    assert _assert_invoke(accept="image/png", expect_binary=False)

    patch_operations = [
        {"op": "add", "path": "/binaryMediaTypes/image~1png"},
        # seems like wildcard with star on the left is not supported
        {"op": "add", "path": "/binaryMediaTypes/*~1test"},
    ]
    aws_client.apigateway.update_rest_api(restApiId=api_id, patchOperations=patch_operations)
    # this deployment has `binaryMediaTypes` configured, so it should now return binary data if the client sends the
    # right `Accept` header and the lambda returns the Content-Type
    if is_aws_cloud():
        time.sleep(10)
    stage_2 = "test2"
    endpoint = api_invoke_url(api_id=api_id, path="/test", stage=stage_2)
    aws_client.apigateway.create_deployment(restApiId=api_id, stageName=stage_2)

    # we poll that the API is returning the right data after deployment
    poll_condition(
        lambda: _assert_invoke(accept="image/png", expect_binary=True), timeout=timeout, interval=1
    )
    if is_aws_cloud():
        time.sleep(10)

    # all conditions are met
    assert _assert_invoke(accept="image/png", expect_binary=True)

    # client is sending the wrong accept, so the API returns the base64 data
    assert _assert_invoke(accept="image/jpg", expect_binary=False)

    # client is sending the wrong accept (wildcard), so the API returns the base64 data
    assert _assert_invoke(accept="image/*", expect_binary=False)

    # wildcard on the left is not supported
    assert _assert_invoke(accept="*/test", expect_binary=False)

    # client is sending an accept that matches the wildcard, but it does not work
    assert _assert_invoke(accept="random/test", expect_binary=False)

    # Accept has to exactly match what is configured
    assert _assert_invoke(accept="*/*", expect_binary=False)

    # client is sending a multiple accept, but AWS only checks the first one
    assert _assert_invoke(accept="image/webp,image/png,*/*;q=0.8", expect_binary=False)

    # client is sending a multiple accept, but AWS only checks the first one, which is right
    assert _assert_invoke(accept="image/png,image/*,*/*;q=0.8", expect_binary=True)

    # lambda is returning that the payload is not b64 encoded
    decoded_response["isBase64Encoded"] = False
    assert _assert_invoke(accept="image/png", expect_binary=False)

    patch_operations = [
        {"op": "add", "path": "/binaryMediaTypes/application~1*"},
        {"op": "add", "path": "/binaryMediaTypes/image~1jpg"},
        {"op": "remove", "path": "/binaryMediaTypes/*~1test"},
    ]
    aws_client.apigateway.update_rest_api(restApiId=api_id, patchOperations=patch_operations)
    if is_aws_cloud():
        # AWS starts returning 200, but then fails again with 403. Wait a bit for it to be stable
        time.sleep(10)

    # this deployment has `binaryMediaTypes` configured, so it should now return binary data if the client sends the
    # right `Accept` header
    stage_3 = "test3"
    endpoint = api_invoke_url(api_id=api_id, path="/test", stage=stage_3)
    aws_client.apigateway.create_deployment(restApiId=api_id, stageName=stage_3)
    decoded_response["isBase64Encoded"] = True

    # we poll that the API is returning the right data after deployment
    poll_condition(
        lambda: _assert_invoke(accept="image/png", expect_binary=True), timeout=timeout, interval=1
    )
    if is_aws_cloud():
        time.sleep(10)

    # different scenario with right side wildcard, all working
    decoded_response["headers"]["Content-Type"] = "application/test"
    assert _assert_invoke(accept="application/whatever", expect_binary=True)
    assert _assert_invoke(accept="application/test", expect_binary=True)
    assert _assert_invoke(accept="application/*", expect_binary=True)

    # lambda is returning a content-type that matches one binaryMediaType, but Accept matches another binaryMediaType
    # it seems it does not matter, only Accept is checked
    decoded_response["headers"]["Content-Type"] = "image/png"
    assert _assert_invoke(accept="image/jpg", expect_binary=True)

    # lambda is returning a content-type that matches the wildcard, but Accept matches another binaryMediaType
    decoded_response["headers"]["Content-Type"] = "application/whatever"
    assert _assert_invoke(accept="image/png", expect_binary=True)

    # ContentType does not matter at all
    decoded_response["headers"].pop("Content-Type")
    assert _assert_invoke(accept="image/png", expect_binary=True)

    # bad Accept
    assert _assert_invoke(accept="application", expect_binary=False)

    # no Accept
    assert _assert_invoke(accept=None, expect_binary=False)

    # bad base64
    decoded_response["body"] = "èé+à)("
    bad_b64_response = requests.post(
        url=endpoint,
        data=json.dumps(decoded_response),
        headers={"User-Agent": "python/test", "Accept": "image/png"},
    )
    assert bad_b64_response.status_code == 500