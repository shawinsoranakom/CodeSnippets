def test_invoke_endpoint_cors_headers(
        self, url_type, disable_custom_cors, origin, monkeypatch, aws_client
    ):
        if not is_next_gen_api() and url_type == UrlType.LS_PATH_BASED:
            pytest.skip("This URL type is not supported with the legacy implementation")

        monkeypatch.setattr(config, "DISABLE_CUSTOM_CORS_APIGATEWAY", disable_custom_cors)
        monkeypatch.setattr(
            cors, "ALLOWED_CORS_ORIGINS", cors.ALLOWED_CORS_ORIGINS + ["http://allowed"]
        )

        responses = [
            {
                "statusCode": "200",
                "httpMethod": "OPTIONS",
                "responseParameters": {
                    "method.response.header.Access-Control-Allow-Origin": "'http://test.com'",
                    "method.response.header.Vary": "'Origin'",
                },
            }
        ]
        api_id = self.create_api_gateway_and_deploy(
            aws_client.apigateway,
            aws_client.dynamodb,
            integration_type="MOCK",
            integration_responses=responses,
            stage_name=TEST_STAGE_NAME,
            request_templates={"application/json": json.dumps({"statusCode": 200})},
        )

        # invoke endpoint with Origin header
        endpoint = api_invoke_url(api_id, stage=TEST_STAGE_NAME, path="/", url_type=url_type)
        response = requests.options(endpoint, headers={"Origin": origin})

        # assert response codes and CORS headers
        if disable_custom_cors:
            if origin == "http://allowed":
                assert response.status_code == 204
                assert "http://allowed" in response.headers["Access-Control-Allow-Origin"]
            else:
                assert response.status_code == 403
        else:
            assert response.status_code == 200
            assert "http://test.com" in response.headers["Access-Control-Allow-Origin"]