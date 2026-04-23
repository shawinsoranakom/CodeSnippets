def test_parse_request(self, dummy_deployment, parse_handler_chain, get_invocation_context):
        host_header = f"{TEST_API_ID}.execute-api.host.com"
        headers = Headers(
            {
                "test-header": "value1",
                "test-header-multi": ["value2", "value3"],
                "host": host_header,
            }
        )
        body = b"random-body"
        request = Request(
            body=body,
            headers=headers,
            query_string="test-param=1&test-param-2=2&test-multi=val1&test-multi=val2",
            path=f"/{TEST_API_STAGE}/normal-path",
        )
        context = get_invocation_context(request)
        context.deployment = dummy_deployment

        parse_handler_chain.handle(context, Response())

        assert context.request == request
        assert context.account_id == TEST_AWS_ACCOUNT_ID
        assert context.region == TEST_AWS_REGION_NAME

        assert context.invocation_request["http_method"] == "GET"
        assert context.invocation_request["headers"] == Headers(
            {
                "host": host_header,
                "test-header": "value1",
                "test-header-multi": ["value2", "value3"],
            }
        )
        assert context.invocation_request["body"] == body
        assert (
            context.invocation_request["path"]
            == context.invocation_request["raw_path"]
            == "/normal-path"
        )

        assert context.context_variables["domainName"] == host_header
        assert context.context_variables["domainPrefix"] == TEST_API_ID
        assert context.context_variables["path"] == f"/{TEST_API_STAGE}/normal-path"

        assert "Root=" in context.trace_id