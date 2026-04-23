def test_cfn_apigateway_aws_integration(deploy_cfn_template, aws_client):
    api_name = f"rest-api-{short_uid()}"
    custom_id = short_uid()

    deploy_cfn_template(
        template_path=os.path.join(
            os.path.dirname(__file__),
            "../../../templates/apigw-awsintegration-request-parameters.yaml",
        ),
        parameters={
            "ApiName": api_name,
            "CustomTagKey": "_custom_id_",
            "CustomTagValue": custom_id,
        },
    )

    # check resources creation
    apis = [
        api for api in aws_client.apigateway.get_rest_apis()["items"] if api["name"] == api_name
    ]
    assert len(apis) == 1
    api_id = apis[0]["id"]

    # check resources creation
    resources = aws_client.apigateway.get_resources(restApiId=api_id)["items"]
    assert (
        resources[0]["resourceMethods"]["GET"]["requestParameters"]["method.request.path.id"]
        is False
    )
    assert (
        resources[0]["resourceMethods"]["GET"]["methodIntegration"]["requestParameters"][
            "integration.request.path.object"
        ]
        == "method.request.path.id"
    )

    # check domains creation
    domain_names = [
        domain["domainName"] for domain in aws_client.apigateway.get_domain_names()["items"]
    ]
    expected_domain = "cfn5632.localstack.cloud"  # hardcoded value from template yaml file
    assert expected_domain in domain_names

    # check basepath mappings creation
    mappings = [
        mapping["basePath"]
        for mapping in aws_client.apigateway.get_base_path_mappings(domainName=expected_domain)[
            "items"
        ]
    ]
    assert len(mappings) == 1
    assert mappings[0] == "(none)"