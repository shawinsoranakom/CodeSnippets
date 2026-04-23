def _test_api_gateway_lambda_proxy_integration(
        self,
        fn_name: str,
        path: str,
        role_arn: str,
        apigw_client,
    ) -> None:
        test_result = self._test_api_gateway_lambda_proxy_integration_no_asserts(
            fn_name, path, role_arn, apigw_client
        )
        data, resource, result, url, path_with_replace = test_result

        assert result.status_code == 203
        assert result.headers.get("foo") == "bar123"
        assert "set-cookie" in result.headers

        try:
            parsed_body = json.loads(to_str(result.content))
        except json.decoder.JSONDecodeError as e:
            raise Exception(f"Couldn't json-decode content: {to_str(result.content)}") from e
        assert parsed_body.get("return_status_code") == 203
        assert parsed_body.get("return_headers") == {"foo": "bar123"}
        assert parsed_body.get("queryStringParameters") == {"foo": "foo", "bar": "baz"}

        request_context = parsed_body.get("requestContext")
        source_ip = request_context["identity"].pop("sourceIp")

        assert re.match(r"^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$", source_ip)

        expected_path = f"/{TEST_STAGE_NAME}/lambda/foo1"
        assert expected_path == request_context["path"]
        assert request_context.get("stageVariables") is None
        assert TEST_AWS_ACCOUNT_ID == request_context["accountId"]
        assert resource.get("id") == request_context["resourceId"]
        assert request_context["stage"] == TEST_STAGE_NAME
        assert "python-requests/testing" == request_context["identity"]["userAgent"]
        assert "POST" == request_context["httpMethod"]
        assert "HTTP/1.1" == request_context["protocol"]
        assert "requestTimeEpoch" in request_context
        assert "requestTime" in request_context
        assert "requestId" in request_context

        # assert that header keys are lowercase (as in AWS)
        headers = parsed_body.get("headers") or {}
        header_names = list(headers.keys())
        assert "Host" in header_names
        assert "Content-Length" in header_names
        assert "User-Agent" in header_names

        result = requests.delete(url, data=json.dumps(data))
        assert 204 == result.status_code

        # send message with non-ASCII chars
        body_msg = "🙀 - 参よ"
        result = requests.post(url, data=json.dumps({"return_raw_body": body_msg}))
        assert body_msg == to_str(result.content)

        # send message with binary data
        binary_msg = b"\xff \xaa \x11"
        result = requests.post(url, data=binary_msg)
        result_content = json.loads(to_str(result.content))
        assert "/yCqIBE=" == result_content["body"]
        assert ["isBase64Encoded"]