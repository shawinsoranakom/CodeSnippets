def test_api_gateway_request_validator(
        self, create_lambda_function, create_rest_apigw, apigw_redeploy_api, snapshot, aws_client
    ):
        snapshot.add_transformers_list(
            [
                snapshot.transform.key_value("requestValidatorId"),
                snapshot.transform.key_value("cacheNamespace"),
                snapshot.transform.key_value("id"),  # deployment id
                snapshot.transform.key_value("fn_name"),  # lambda name
                snapshot.transform.key_value("fn_arn"),  # lambda arn
            ]
        )

        fn_name = f"test-{short_uid()}"
        create_lambda_function(
            func_name=fn_name,
            handler_file=TEST_LAMBDA_AWS_PROXY,
            runtime=Runtime.python3_12,
        )
        lambda_arn = aws_client.lambda_.get_function(FunctionName=fn_name)["Configuration"][
            "FunctionArn"
        ]
        # matching on lambda id for reference replacement in snapshots
        snapshot.match("register-lambda", {"fn_name": fn_name, "fn_arn": lambda_arn})

        parsed_arn = parse_arn(lambda_arn)
        region = parsed_arn["region"]
        account_id = parsed_arn["account"]

        api_id, _, root = create_rest_apigw(name="aws lambda api")

        resource_1 = aws_client.apigateway.create_resource(
            restApiId=api_id, parentId=root, pathPart="nested"
        )["id"]

        resource_id = aws_client.apigateway.create_resource(
            restApiId=api_id, parentId=resource_1, pathPart="{test}"
        )["id"]

        validator_id = aws_client.apigateway.create_request_validator(
            restApiId=api_id,
            name="test-validator",
            validateRequestParameters=True,
            validateRequestBody=True,
        )["id"]

        # create Model schema to validate body
        aws_client.apigateway.create_model(
            restApiId=api_id,
            name="testSchema",
            contentType="application/json",
            schema=json.dumps(
                {
                    "$schema": "http://json-schema.org/draft-04/schema#",
                    "title": "testSchema",
                    "type": "object",
                    "properties": {
                        "a": {"type": "number"},
                        "b": {"type": "number"},
                    },
                    "required": ["a", "b"],
                }
            ),
        )

        for http_method in ("GET", "POST"):
            aws_client.apigateway.put_method(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                authorizationType="NONE",
                requestValidatorId=validator_id,
                requestParameters={
                    # the path parameter is most often used to generate SDK from the REST API
                    "method.request.path.test": True,
                    "method.request.querystring.qs1": True,
                    "method.request.header.x-header-param": True,
                },
                requestModels={"application/json": "testSchema"},
            )

            aws_client.apigateway.put_integration(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                integrationHttpMethod="POST",
                type="AWS_PROXY",
                uri=f"arn:{get_partition(region)}:apigateway:{region}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations",
            )
            aws_client.apigateway.put_method_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                statusCode="200",
            )
            aws_client.apigateway.put_integration_response(
                restApiId=api_id,
                resourceId=resource_id,
                httpMethod=http_method,
                statusCode="200",
            )

        stage_name = "local"
        deploy_1 = aws_client.apigateway.create_deployment(restApiId=api_id, stageName=stage_name)
        snapshot.match("deploy-1", deploy_1)

        source_arn = (
            f"arn:{get_partition(region)}:execute-api:{region}:{account_id}:{api_id}/*/*/nested/*"
        )

        aws_client.lambda_.add_permission(
            FunctionName=lambda_arn,
            StatementId=str(short_uid()),
            Action="lambda:InvokeFunction",
            Principal="apigateway.amazonaws.com",
            SourceArn=source_arn,
        )

        url = api_invoke_url(api_id, stage=stage_name, path="/nested/value")
        # test that with every request parameters and a valid body, it passes
        response = requests.post(
            url,
            json={"a": 1, "b": 2},
            headers={"x-header-param": "test"},
            params={"qs1": "test"},
        )
        assert response.ok
        assert json.loads(response.json()["body"]) == {"a": 1, "b": 2}

        # GET request with no body
        response_get = requests.get(
            url,
            headers={"x-header-param": "test"},
            params={"qs1": "test"},
        )
        assert response_get.status_code == 400

        # replace the POST method requestParameters to require a non-existing {issuer} path part
        response = aws_client.apigateway.update_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod="POST",
            patchOperations=[
                {
                    "op": "add",
                    "path": "/requestParameters/method.request.path.issuer",
                    "value": "true",
                },
                {
                    "op": "remove",
                    "path": "/requestParameters/method.request.path.test",
                    "value": "true",
                },
            ],
        )
        snapshot.match("change-request-path-names", response)
        apigw_redeploy_api(rest_api_id=api_id, stage_name=stage_name)

        response = requests.post(url, json={"test": "test"})
        assert response.status_code == 400
        snapshot.match("missing-all-required-request-params-post", response.json())

        response = requests.get(url, params={"qs1": "test"})
        assert response.status_code == 400
        snapshot.match("missing-required-headers-request-params-get", response.json())

        response = requests.get(url, headers={"x-header-param": "test"})
        assert response.status_code == 400
        snapshot.match("missing-required-qs-request-params-get", response.json())

        # revert the path validation for POST method
        response = aws_client.apigateway.update_method(
            restApiId=api_id,
            resourceId=resource_id,
            httpMethod="POST",
            patchOperations=[
                {
                    "op": "add",
                    "path": "/requestParameters/method.request.path.test",
                    "value": "true",
                },
                {
                    "op": "remove",
                    "path": "/requestParameters/method.request.path.issuer",
                    "value": "true",
                },
            ],
        )
        snapshot.match("revert-request-path-names", response)
        apigw_redeploy_api(rest_api_id=api_id, stage_name=stage_name)
        retries = 10 if is_aws_cloud() else 3
        sleep_time = 10 if is_aws_cloud() else 1

        def _wrong_path_removed():
            # the validator should work with a valid object
            _response = requests.post(
                url,
                json={"a": 1, "b": 2},
                headers={"x-header-param": "test"},
                params={"qs1": "test"},
            )
            assert _response.status_code == 200

        retry(_wrong_path_removed, retries=retries, sleep=sleep_time)

        def _invalid_body():
            # the validator should fail with this message not respecting the schema
            _response = requests.post(
                url,
                json={"test": "test"},
                headers={"x-header-param": "test"},
                params={"qs1": "test"},
            )
            assert _response.status_code == 400
            content = _response.json()
            assert content["message"] == "Invalid request body"
            return content

        response_content = retry(_invalid_body, retries=retries, sleep=sleep_time)
        snapshot.match("invalid-request-body", response_content)

        # GET request with an empty body
        response_get = requests.get(
            url,
            headers={"x-header-param": "test"},
            params={"qs1": "test"},
        )
        assert response_get.status_code == 400
        assert response_get.json()["message"] == "Invalid request body"

        # GET request with an empty body, content type JSON
        response_get = requests.get(
            url,
            headers={"Content-Type": "application/json", "x-header-param": "test"},
            params={"qs1": "test"},
        )
        assert response_get.status_code == 400

        # update request validator to disable validation
        patch_operations = [
            {"op": "replace", "path": "/validateRequestBody", "value": "false"},
            {"op": "replace", "path": "/validateRequestParameters", "value": "false"},
        ]
        response = aws_client.apigateway.update_request_validator(
            restApiId=api_id, requestValidatorId=validator_id, patchOperations=patch_operations
        )
        snapshot.match("disable-request-validator", response)
        apigw_redeploy_api(rest_api_id=api_id, stage_name=stage_name)

        def _disabled_validation():
            _response = requests.post(url, json={"test": "test"})
            assert _response.ok
            return _response.json()

        response = retry(_disabled_validation, retries=retries, sleep=sleep_time)
        assert json.loads(response["body"]) == {"test": "test"}

        # GET request with an empty body
        response_get = requests.get(url)
        assert response_get.ok