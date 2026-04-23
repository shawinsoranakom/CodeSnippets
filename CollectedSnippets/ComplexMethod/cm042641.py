async def _check_POST_json(
        client: H2ClientProtocol,
        request: Request,
        expected_request_body: dict[str, str],
        expected_extra_data: str,
        expected_status: int,
    ) -> None:
        response = await make_request(client, request)

        assert response.status == expected_status

        content_length_header = response.headers.get("Content-Length")
        assert content_length_header is not None
        content_length = int(content_length_header)
        assert len(response.body) == content_length

        # Parse the body
        content_encoding_header = response.headers[b"Content-Encoding"]
        assert content_encoding_header is not None
        content_encoding = str(content_encoding_header, "utf-8")
        body = json.loads(str(response.body, content_encoding))
        assert "request-body" in body
        assert "extra-data" in body
        assert "request-headers" in body

        request_body = body["request-body"]
        assert request_body == expected_request_body

        extra_data = body["extra-data"]
        assert extra_data == expected_extra_data

        # Check if headers were sent successfully
        request_headers = body["request-headers"]
        for k, v in request.headers.items():
            k_str = str(k, "utf-8")
            assert k_str in request_headers
            assert request_headers[k_str] == str(v[0], "utf-8")