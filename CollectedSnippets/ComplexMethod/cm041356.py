def test_render_response_template(self, format):
        variables = MappingTemplateVariables(
            input=MappingTemplateInput(
                body='{"spam": "eggs"}',
                params=MappingTemplateParams(
                    path={"proxy": "path"},
                    querystring={"baz": "test"},
                    header={"content-type": format, "accept": format},
                ),
            ),
            context=ContextVariables(
                httpMethod="POST",
                stage="local",
                authorizer=ContextVarsAuthorizer(principalId="12233"),
                identity=ContextVarsIdentity(accountId="00000", apiKey="11111"),
                resourcePath="/{proxy}",
            ),
            stageVariables={"stageVariable1": "value1", "stageVariable2": "value2"},
        )
        context_overrides = ContextVariableOverrides(
            requestOverride=ContextVarsRequestOverride(header={}, path={}, querystring={}),
            responseOverride=ContextVarsResponseOverride(header={}, status=0),
        )
        template = TEMPLATE_JSON if format == APPLICATION_JSON else TEMPLATE_XML
        template += RESPONSE_OVERRIDE

        rendered_response, response_override = ApiGatewayVtlTemplate().render_response(
            template=template, variables=variables, context_overrides=context_overrides
        )
        if format == APPLICATION_JSON:
            rendered_response = json.loads(rendered_response)
            assert rendered_response.get("body") == {"spam": "eggs"}
            assert rendered_response.get("method") == "POST"
            assert rendered_response.get("principalId") == "12233"
        else:
            rendered_response = xmltodict.parse(rendered_response).get("root", {})
            # TODO Verify that those difference between xml and json are expected
            assert rendered_response.get("body") == '{"spam": "eggs"}'
            assert rendered_response.get("@method") == "POST"
            assert rendered_response.get("@principalId") == "12233"

        assert rendered_response.get("stage") == "local"
        assert rendered_response.get("enhancedAuthContext") == {"principalId": "12233"}
        assert rendered_response.get("identity") == {"accountId": "00000", "apiKey": "11111"}
        assert rendered_response.get("headers") == {
            "content-type": format,
            "accept": format,
        }
        assert rendered_response.get("query") == {"baz": "test"}
        assert rendered_response.get("path") == {"proxy": "path"}
        assert rendered_response.get("stageVariables") == {
            "stageVariable1": "value1",
            "stageVariable2": "value2",
        }

        assert response_override == {
            "header": {"multivalue": ["1header", "2header"], "oHeader": "1header"},
            "status": 400,
        }