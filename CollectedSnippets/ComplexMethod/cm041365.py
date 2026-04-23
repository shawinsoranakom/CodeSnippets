def test_query_protocol_json_serialization(headers_dict):
    service = load_service("sts")
    response_serializer = create_serializer(service)
    headers = Headers(headers_dict)
    utc_timestamp = 1661255665.123
    response_data = GetSessionTokenResponse(
        Credentials=Credentials(
            AccessKeyId="accessKeyId",
            SecretAccessKey="secretAccessKey",
            SessionToken="sessionToken",
            Expiration=datetime.utcfromtimestamp(utc_timestamp),
        )
    )
    result: Response = response_serializer.serialize_to_response(
        response_data, service.operation_model("GetSessionToken"), headers, long_uid()
    )
    assert result is not None
    assert result.content_type is not None
    assert result.content_type == "application/json"
    parsed_data = json.loads(result.data)
    # Ensure the structure is the same as for query-xml (f.e. with "SOAP"-like root element), but just JSON encoded
    assert "GetSessionTokenResponse" in parsed_data
    assert "ResponseMetadata" in parsed_data["GetSessionTokenResponse"]
    assert "GetSessionTokenResult" in parsed_data["GetSessionTokenResponse"]
    # Make sure the timestamp is formatted as str(int(utc float))
    assert parsed_data["GetSessionTokenResponse"]["GetSessionTokenResult"].get(
        "Credentials", {}
    ).get("Expiration") == str(int(utc_timestamp))