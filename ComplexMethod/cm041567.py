def test_cfn_apigateway_rest_api(deploy_cfn_template, aws_client, snapshot):
    snapshot.add_transformers_list(
        [
            snapshot.transform.key_value("aws:cloudformation:logical-id"),
            snapshot.transform.key_value("aws:cloudformation:stack-name"),
            snapshot.transform.resource_name(),
            snapshot.transform.key_value("id"),
            snapshot.transform.key_value("rootResourceId"),
        ]
    )

    stack = deploy_cfn_template(
        template_path=os.path.join(os.path.dirname(__file__), "../../../templates/apigateway.json")
    )

    rs = aws_client.apigateway.get_rest_apis()
    apis = [item for item in rs["items"] if item["name"] == "DemoApi_dev"]
    assert not apis

    stack.destroy()

    stack_2 = deploy_cfn_template(
        template_path=os.path.join(os.path.dirname(__file__), "../../../templates/apigateway.json"),
        parameters={"Create": "True"},
    )
    rs = aws_client.apigateway.get_rest_apis()
    apis = [item for item in rs["items"] if item["name"] == "DemoApi_dev"]
    assert len(apis) == 1
    snapshot.match("rest-api", apis[0])

    rs = aws_client.apigateway.get_models(restApiId=apis[0]["id"])
    assert len(rs["items"]) == 3

    stack_2.destroy()