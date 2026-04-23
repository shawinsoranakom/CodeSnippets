def test_restjson_headers_target_serialization():
    # SendApiAssetResponse
    response = {
        "Body": "hello",
        "ResponseHeaders": {
            "foo": "bar",
            "baz": "ed",
        },
    }

    # skipping assert here, because the response will contain all HTTP headers (given the nature of "ResponseHeaders"
    # attribute).
    result = _botocore_serializer_integration_test(
        service="dataexchange",
        action="SendApiAsset",
        response=response,
        expected_response_content=_skip_assert,
    )

    assert result["Body"] == "hello"
    assert result["ResponseHeaders"]["foo"] == "bar"
    assert result["ResponseHeaders"]["baz"] == "ed"

    headers = result["ResponseMetadata"]["HTTPHeaders"]
    assert "foo" in headers
    assert "baz" in headers
    assert headers["foo"] == "bar"
    assert headers["baz"] == "ed"