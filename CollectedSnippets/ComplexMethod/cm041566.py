def test_cfn_with_apigateway_resources(deploy_cfn_template, aws_client, snapshot):
    snapshot.add_transformer(snapshot.transform.apigateway_api())
    snapshot.add_transformer(snapshot.transform.key_value("cacheNamespace"))

    stack = deploy_cfn_template(
        template_path=os.path.join(os.path.dirname(__file__), "../../../templates/template35.yaml")
    )
    apis = [
        api
        for api in aws_client.apigateway.get_rest_apis()["items"]
        if api["name"] == "celeste-Gateway-local"
    ]
    assert len(apis) == 1
    api_id = apis[0]["id"]

    resources = [
        res
        for res in aws_client.apigateway.get_resources(restApiId=api_id)["items"]
        if res.get("pathPart") == "account"
    ]

    assert len(resources) == 1

    resp = aws_client.apigateway.get_method(
        restApiId=api_id, resourceId=resources[0]["id"], httpMethod="POST"
    )
    snapshot.match("get-method-post", resp)

    models = aws_client.apigateway.get_models(restApiId=api_id)
    models["items"].sort(key=itemgetter("name"))
    snapshot.match("get-models", models)

    schemas = [model["schema"] for model in models["items"]]
    for schema in schemas:
        # assert that we can JSON load the schema, and that the schema is a valid JSON
        assert isinstance(json.loads(schema), dict)

    stack.destroy()