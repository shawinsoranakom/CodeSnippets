def test_create_rest_api_with_custom_id(self, create_rest_apigw, url_function, aws_client):
        if not is_next_gen_api() and url_function == localstack_path_based_url:
            pytest.skip("This URL type is not supported in the legacy implementation")
        apigw_name = f"gw-{short_uid()}"
        test_id = "test-id123"
        api_id, name, _ = create_rest_apigw(name=apigw_name, tags={TAG_KEY_CUSTOM_ID: test_id})
        assert test_id == api_id
        assert apigw_name == name
        response = aws_client.apigateway.get_rest_api(restApiId=test_id)
        assert response["name"] == apigw_name

        spec_file = load_file(TEST_IMPORT_MOCK_INTEGRATION)
        aws_client.apigateway.put_rest_api(restApiId=test_id, body=spec_file, mode="overwrite")

        aws_client.apigateway.create_deployment(restApiId=test_id, stageName="latest")

        url = url_function(test_id, stage_name="latest", path="/echo/foobar")
        response = requests.get(url)

        assert response.ok
        assert response._content == b'{"echo": "foobar", "response": "mocked"}'