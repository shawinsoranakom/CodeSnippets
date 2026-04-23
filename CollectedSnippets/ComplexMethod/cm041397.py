def test_disable_cors_headers(self, monkeypatch):
        """Test DISABLE_CORS_CHECKS=1 (most restrictive setting, not sending any CORS headers)"""
        headers = mock_aws_request_headers(
            "sns", aws_access_key_id=TEST_AWS_ACCESS_KEY_ID, region_name=TEST_AWS_REGION_NAME
        )
        headers["Origin"] = "https://app.localstack.cloud"
        url = config.internal_service_url()
        data = {"Action": "ListTopics", "Version": "2010-03-31"}
        response = requests.post(url, headers=headers, data=data)
        assert response.status_code == 200
        assert response.headers["access-control-allow-origin"] == headers["Origin"]
        assert "authorization" in response.headers["access-control-allow-headers"].lower()
        assert "GET" in response.headers["access-control-allow-methods"].split(",")
        assert "<ListTopicsResponse" in to_str(response.content)

        monkeypatch.setattr(config, "DISABLE_CORS_HEADERS", True)
        response = requests.post(url, headers=headers, data=data)
        assert response.status_code == 200
        assert "<ListTopicsResponse" in to_str(response.content)
        assert not response.headers.get("access-control-allow-headers")
        assert not response.headers.get("access-control-allow-methods")
        assert not response.headers.get("access-control-allow-origin")
        assert not response.headers.get("access-control-allow-credentials")