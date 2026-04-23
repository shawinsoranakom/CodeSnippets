def test_cors_apigw_not_applied(self, aws_client):
        # make sure the service is loaded and has registered routes
        aws_client.apigateway.get_rest_apis()

        cors_headers = [
            "access-control-allow-headers",
            "access-control-allow-methods",
            "access-control-allow-origin",
            "access-control-allow-credentials",
        ]

        # assert that the registered routes for APIGW are handled by themselves on the CORS/CRSF level
        # note: we have tests for asserting proper return of CORS headers in APIGW itself when configured to do so
        #
        rest_api_url_user_request = (
            f"{config.internal_service_url()}/restapis/myapiid/stage/_user_request_"
        )
        response = requests.get(
            rest_api_url_user_request,
            verify=False,
            headers={
                "Origin": "https://app.localstack.cloud",
            },
        )
        assert response.status_code == 404

        assert not any(response.headers.get(cors_header) for cors_header in cors_headers)

        rest_api_url_host = f"{config.internal_service_url()}/stage"
        host_header = "myapiid.execute-api.localhost.localstack.cloud:4566"
        response = requests.get(
            rest_api_url_host,
            verify=False,
            headers={
                "Origin": "https://app.localstack.cloud",
                "Host": host_header,
            },
        )

        assert response.status_code == 404
        assert not any(response.headers.get(cors_header) for cors_header in cors_headers)

        # now we give it a try with a route from the provider defined in the specs: GetRestApi, and an authorized origin
        rest_api_url = f"{config.internal_service_url()}/restapis/myapiid"
        response = requests.get(
            rest_api_url,
            verify=False,
            headers={
                "Origin": "https://app.localstack.cloud",
                "Authorization": "AWS4-HMAC-SHA256 Credential=test/20240418/us-east-1/apigateway/aws4_request, SignedHeaders=accept;host;x-amz-date, Signature=88259852931bc389bd7c2e1fb8b700b935e9d6b14bd2ef72efc3a9b20b415701",
            },
        )
        assert response.status_code == 404
        assert all(response.headers.get(cors_header) for cors_header in cors_headers)

        # now do the same from an unauthorized Origin
        response = requests.get(
            rest_api_url,
            verify=False,
            headers={
                "Origin": "http://localhost:4200",
                "Authorization": "AWS4-HMAC-SHA256 Credential=test/20240418/us-east-1/apigateway/aws4_request, SignedHeaders=accept;host;x-amz-date, Signature=88259852931bc389bd7c2e1fb8b700b935e9d6b14bd2ef72efc3a9b20b415701",
            },
        )
        assert response.status_code == 403
        assert not any(response.headers.get(cors_header) for cors_header in cors_headers)