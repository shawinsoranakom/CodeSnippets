def test_api_gateway_http_integrations(
        self, int_type, echo_http_server, monkeypatch, aws_client
    ):
        monkeypatch.setattr(config, "DISABLE_CUSTOM_CORS_APIGATEWAY", False)

        api_path_backend = "/hello_world"
        backend_base_url = echo_http_server
        backend_url = f"{backend_base_url}/{api_path_backend}"

        # create API Gateway and connect it to the HTTP_PROXY/HTTP backend
        result = self.connect_api_gateway_to_http(
            int_type, "test_gateway2", backend_url, path=api_path_backend
        )

        url = path_based_url(
            api_id=result["id"],
            stage_name=TEST_STAGE_NAME,
            path=api_path_backend,
        )

        # make sure CORS headers are present
        origin = "localhost"
        result = requests.options(url, headers={"origin": origin})
        assert result.status_code == 200
        assert re.match(result.headers["Access-Control-Allow-Origin"].replace("*", ".*"), origin)
        assert "POST" in result.headers["Access-Control-Allow-Methods"]
        assert "PATCH" in result.headers["Access-Control-Allow-Methods"]

        custom_result = json.dumps({"foo": "bar"})

        # make test GET request to gateway
        result = requests.get(url)
        assert 200 == result.status_code
        expected = custom_result if int_type == "custom" else "{}"
        assert expected == json.loads(to_str(result.content))["data"]

        # make test POST request to gateway
        data = json.dumps({"data": 123})
        result = requests.post(url, data=data)
        assert 200 == result.status_code
        expected = custom_result if int_type == "custom" else data
        assert expected == json.loads(to_str(result.content))["data"]

        # make test POST request with non-JSON content type
        data = "test=123"
        ctype = "application/x-www-form-urlencoded"
        result = requests.post(url, data=data, headers={"content-type": ctype})
        assert 200 == result.status_code
        content = json.loads(to_str(result.content))
        headers = CaseInsensitiveDict(content["headers"])
        expected = custom_result if int_type == "custom" else data
        assert expected == content["data"]
        assert ctype == headers["content-type"]