def test_invocation_trace_id(
        self,
        aws_client,
        create_rest_apigw,
        create_lambda_function,
        create_role_with_policy,
        region_name,
        snapshot,
    ):
        snapshot.add_transformers_list(
            [
                snapshot.transform.key_value("via"),
                snapshot.transform.key_value("x-amz-cf-id"),
                snapshot.transform.key_value("x-amz-cf-pop"),
                snapshot.transform.key_value("x-amz-apigw-id"),
                snapshot.transform.key_value("x-amzn-trace-id"),
                snapshot.transform.key_value("FunctionName"),
                snapshot.transform.key_value("FunctionArn"),
                snapshot.transform.key_value("date", reference_replacement=False),
                snapshot.transform.key_value("content-length", reference_replacement=False),
            ]
        )
        api_id, _, root_id = create_rest_apigw(name="test trace id")

        resource = aws_client.apigateway.create_resource(
            restApiId=api_id, parentId=root_id, pathPart="path"
        )
        hardcoded_resource_id = resource["id"]

        response_template_get = {"statusCode": 200}
        _create_mock_integration_with_200_response_template(
            aws_client, api_id, hardcoded_resource_id, "GET", response_template_get
        )

        fn_name = f"test-trace-id-{short_uid()}"
        # create lambda
        create_function_response = create_lambda_function(
            func_name=fn_name,
            handler_file=TEST_LAMBDA_AWS_PROXY,
            handler="lambda_aws_proxy.handler",
            runtime=Runtime.python3_12,
        )
        # create invocation role
        _, role_arn = create_role_with_policy(
            "Allow", "lambda:InvokeFunction", json.dumps(APIGATEWAY_ASSUME_ROLE_POLICY), "*"
        )
        lambda_arn = create_function_response["CreateFunctionResponse"]["FunctionArn"]
        # matching on lambda id for reference replacement in snapshots
        snapshot.match("register-lambda", {"FunctionName": fn_name, "FunctionArn": lambda_arn})

        resource = aws_client.apigateway.create_resource(
            restApiId=api_id, parentId=root_id, pathPart="{proxy+}"
        )
        proxy_resource_id = resource["id"]

        aws_client.apigateway.put_method(
            restApiId=api_id,
            resourceId=proxy_resource_id,
            httpMethod="ANY",
            authorizationType="NONE",
        )

        # Lambda AWS_PROXY integration
        aws_client.apigateway.put_integration(
            restApiId=api_id,
            resourceId=proxy_resource_id,
            httpMethod="ANY",
            type="AWS_PROXY",
            integrationHttpMethod="POST",
            uri=f"arn:aws:apigateway:{region_name}:lambda:path/2015-03-31/functions/{lambda_arn}/invocations",
            credentials=role_arn,
        )

        stage_name = "dev"
        aws_client.apigateway.create_deployment(restApiId=api_id, stageName=stage_name)

        def _invoke_api(path: str, headers: dict[str, str]) -> dict[str, str]:
            url = api_invoke_url(api_id=api_id, stage=stage_name, path=path)
            _response = requests.get(url, headers=headers)
            assert _response.ok
            lower_case_headers = {k.lower(): v for k, v in _response.headers.items()}
            return lower_case_headers

        retries = 10 if is_aws_cloud() else 3
        sleep = 3 if is_aws_cloud() else 1
        resp_headers = retry(
            _invoke_api,
            retries=retries,
            sleep=sleep,
            headers={},
            path="/path",
        )

        snapshot.match("normal-req-headers-MOCK", resp_headers)
        assert "x-amzn-trace-id" not in resp_headers

        full_trace = "Root=1-3152b799-8954dae64eda91bc9a23a7e8;Parent=7fa8c0f79203be72;Sampled=1"
        trace_id = "Root=1-3152b799-8954dae64eda91bc9a23a7e8"
        hardcoded_parent = "Parent=7fa8c0f79203be72"

        resp_headers_with_trace_id = _invoke_api(
            path="/path", headers={"x-amzn-trace-id": full_trace}
        )
        snapshot.match("trace-id-req-headers-MOCK", resp_headers_with_trace_id)

        resp_proxy_headers = retry(
            _invoke_api,
            retries=retries,
            sleep=sleep,
            headers={},
            path="/proxy-value",
        )
        snapshot.match("normal-req-headers-AWS_PROXY", resp_proxy_headers)

        resp_headers_with_trace_id = _invoke_api(
            path="/proxy-value", headers={"x-amzn-trace-id": full_trace}
        )
        snapshot.match("trace-id-req-headers-AWS_PROXY", resp_headers_with_trace_id)
        assert full_trace in resp_headers_with_trace_id["x-amzn-trace-id"]
        split_trace = resp_headers_with_trace_id["x-amzn-trace-id"].split(";")
        assert split_trace[1] == hardcoded_parent

        small_trace = trace_id
        resp_headers_with_trace_id = _invoke_api(
            path="/proxy-value", headers={"x-amzn-trace-id": small_trace}
        )
        snapshot.match("trace-id-small-req-headers-AWS_PROXY", resp_headers_with_trace_id)
        assert small_trace in resp_headers_with_trace_id["x-amzn-trace-id"]
        split_trace = resp_headers_with_trace_id["x-amzn-trace-id"].split(";")
        # assert that AWS populated the parent part of the trace with a generated one
        assert split_trace[1] != hardcoded_parent