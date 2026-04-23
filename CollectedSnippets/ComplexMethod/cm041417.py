def test_apigateway_deployed(
        self, aws_client, account_id, region_name, setup_and_teardown, get_deployed_stage
    ):
        function_name = f"sls-test-{get_deployed_stage}-router"
        existing_api_ids = setup_and_teardown

        lambda_client = aws_client.lambda_

        resp = lambda_client.list_functions()
        function = [fn for fn in resp["Functions"] if fn["FunctionName"] == function_name][0]
        assert "handler.createHttpRouter" == function["Handler"]

        apigw_client = aws_client.apigateway
        apis = apigw_client.get_rest_apis()["items"]
        api_ids = [api["id"] for api in apis if api["id"] not in existing_api_ids]
        assert 1 == len(api_ids)

        resources = apigw_client.get_resources(restApiId=api_ids[0])["items"]
        proxy_resources = [res for res in resources if res["path"] == "/foo/bar"]
        assert 1 == len(proxy_resources)

        proxy_resource = proxy_resources[0]
        for method in ["DELETE", "POST", "PUT"]:
            assert method in proxy_resource["resourceMethods"]
            resource_method = proxy_resource["resourceMethods"][method]
            # TODO - needs fixing: this assertion doesn't hold for AWS, as there is no "methodIntegration" key
            # on AWS -> "resourceMethods": {'DELETE': {}, 'POST': {}, 'PUT': {}}
            assert (
                arns.lambda_function_arn(function_name, account_id, region_name)
                in resource_method["methodIntegration"]["uri"]
            )