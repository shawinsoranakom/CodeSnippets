def test_render_custom_template(self, format):
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
        template += REQUEST_OVERRIDE

        rendered_request, context_variable = ApiGatewayVtlTemplate().render_request(
            template=template, variables=variables, context_overrides=context_overrides
        )
        request_override = context_variable["requestOverride"]
        if format == APPLICATION_JSON:
            rendered_request = json.loads(rendered_request)
            assert rendered_request.get("body") == {"spam": "eggs"}
            assert rendered_request.get("method") == "POST"
            assert rendered_request.get("principalId") == "12233"
        else:
            rendered_request = xmltodict.parse(rendered_request).get("root", {})
            # TODO Verify that those difference between xml and json are expected
            assert rendered_request.get("body") == '{"spam": "eggs"}'
            assert rendered_request.get("@method") == "POST"
            assert rendered_request.get("@principalId") == "12233"

        assert rendered_request.get("stage") == "local"
        assert rendered_request.get("enhancedAuthContext") == {"principalId": "12233"}
        assert rendered_request.get("identity") == {"accountId": "00000", "apiKey": "11111"}
        assert rendered_request.get("headers") == {
            "content-type": format,
            "accept": format,
        }
        assert rendered_request.get("query") == {"baz": "test"}
        assert rendered_request.get("path") == {"proxy": "path"}
        assert rendered_request.get("stageVariables") == {
            "stageVariable1": "value1",
            "stageVariable2": "value2",
        }

        assert request_override == {
            "header": {"multivalue": ["1header", "2header"], "oHeader": "1header"},
            "path": {"proxy": "proxy"},
            "querystring": {"query": "query"},
        }