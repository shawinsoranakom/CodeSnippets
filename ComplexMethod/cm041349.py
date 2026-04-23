def test_render_custom_template(self, template, accept_content_type):
        api_context = ApiInvocationContext(
            method="POST",
            path="/foo/bar?baz=test",
            data=b'{"spam": "eggs"}',
            headers={"content-type": APPLICATION_JSON, "accept": accept_content_type},
            stage="local",
        )
        api_context.integration = {
            "requestTemplates": {APPLICATION_JSON: RESPONSE_TEMPLATE_JSON},
            "integrationResponses": {
                "200": {"responseTemplates": {APPLICATION_JSON: RESPONSE_TEMPLATE_JSON}}
            },
        }
        api_context.resource_path = "/{proxy+}"
        api_context.path_params = {"id": "bar"}
        api_context.response = requests_response({"spam": "eggs"})
        api_context.context = {
            "httpMethod": api_context.method,
            "stage": api_context.stage,
            "authorizer": {"principalId": "12233"},
            "identity": {"accountId": "00000", "apiKey": "11111"},
            "resourcePath": api_context.resource_path,
        }
        api_context.stage_variables = {"stageVariable1": "value1", "stageVariable2": "value2"}

        rendered_request = template.render(api_context=api_context)
        result_as_json = json.loads(rendered_request)

        assert result_as_json.get("body") == {"spam": "eggs"}
        assert result_as_json.get("method") == "POST"
        assert result_as_json.get("principalId") == "12233"
        assert result_as_json.get("stage") == "local"
        assert result_as_json.get("enhancedAuthContext") == {"principalId": "12233"}
        assert result_as_json.get("identity") == {"accountId": "00000", "apiKey": "11111"}
        assert result_as_json.get("headers") == {
            "content-type": APPLICATION_JSON,
            "accept": accept_content_type,
        }
        assert result_as_json.get("query") == {"baz": "test"}
        assert result_as_json.get("path") == {"id": "bar"}
        assert result_as_json.get("stageVariables") == {
            "stageVariable1": "value1",
            "stageVariable2": "value2",
        }