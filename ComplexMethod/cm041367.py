def test_json_cbor_blob_parsing(parser_factory):
    serialized_request = {
        "url_path": "/",
        "query_string": "",
        "method": "POST",
        "headers": {
            "Host": "localhost:4566",
            "amz-sdk-invocation-id": "d77968c6-b536-155d-7228-d4dfe6372154",
            "amz-sdk-request": "attempt=1; max=3",
            "Content-Length": "103",
            "Content-Type": "application/x-amz-cbor-1.1",
            "X-Amz-Date": "20220721T081553Z",
            "X-Amz-Target": "Kinesis_20131202.PutRecord",
            "x-localstack-tgt-api": "kinesis",
        },
        "body": b"\xbfjStreamNamedtestdDataMhello, world!lPartitionKeylpartitionkey\xff",
        "url": "/",
        "context": {},
    }

    prepare_request_dict(serialized_request, "")
    split_url = urlsplit(serialized_request.get("url"))
    path = split_url.path
    query_string = split_url.query

    # Use our parser to parse the serialized body
    # Load the appropriate service
    service = load_service("kinesis")
    operation_model = service.operation_model("PutRecord")
    parser = parser_factory(service)
    parsed_operation_model, parsed_request = parser.parse(
        HttpRequest(
            method=serialized_request.get("method") or "GET",
            path=unquote(path),
            query_string=to_str(query_string),
            headers=serialized_request.get("headers"),
            body=serialized_request["body"],
            raw_path=path,
        )
    )

    # Check if the determined operation_model is correct
    assert parsed_operation_model == operation_model

    assert "Data" in parsed_request
    assert parsed_request["Data"] == b"hello, world!"
    assert "StreamName" in parsed_request
    assert parsed_request["StreamName"] == "test"
    assert "PartitionKey" in parsed_request
    assert parsed_request["PartitionKey"] == "partitionkey"