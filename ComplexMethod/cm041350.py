def test_render_custom_template_in_xml(self, template):
        api_context = ApiInvocationContext(
            method="POST",
            path="/foo/bar?baz=test",
            data=b'{"spam": "eggs"}',
            headers={"content-type": APPLICATION_XML, "accept": APPLICATION_XML},
            stage="local",
        )
        api_context.integration = {
            "requestTemplates": {APPLICATION_XML: RESPONSE_TEMPLATE_XML},
            "integrationResponses": {
                "200": {"responseTemplates": {APPLICATION_XML: RESPONSE_TEMPLATE_XML}}
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

        rendered_request = template.render(api_context=api_context, template_key=APPLICATION_XML)
        result_as_xml = xmltodict.parse(rendered_request).get("root", {})

        assert result_as_xml.get("body") == '{"spam": "eggs"}'
        assert result_as_xml.get("@method") == "POST"
        assert result_as_xml.get("@principalId") == "12233"
        assert result_as_xml.get("stage") == "local"
        assert result_as_xml.get("enhancedAuthContext") == {"principalId": "12233"}
        assert result_as_xml.get("identity") == {"accountId": "00000", "apiKey": "11111"}
        assert result_as_xml.get("headers") == {
            "content-type": APPLICATION_XML,
            "accept": APPLICATION_XML,
        }
        assert result_as_xml.get("query") == {"baz": "test"}
        assert result_as_xml.get("path") == {"id": "bar"}
        assert result_as_xml.get("stageVariables") == {
            "stageVariable1": "value1",
            "stageVariable2": "value2",
        }