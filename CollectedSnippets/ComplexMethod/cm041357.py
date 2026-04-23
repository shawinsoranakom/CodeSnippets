def test_skeleton_e2e_sqs_send_message_not_implemented(
    api_class, service_support_status, oracle_message, aws_catalog_mock
):
    catalog = aws_catalog_mock("localstack.aws.skeleton.get_aws_catalog")
    catalog.get_aws_service_status.return_value = service_support_status

    sqs_service = load_service("sqs-query")
    skeleton = Skeleton(sqs_service, api_class)
    request = Request(
        **{
            "method": "POST",
            "path": "/",
            "body": "Action=SendMessage&Version=2012-11-05&QueueUrl=http%3A%2F%2Flocalhost%3A4566%2F000000000000%2Ftf-acc-test-queue&MessageBody=%7B%22foo%22%3A+%22bared%22%7D&DelaySeconds=2",
            "headers": _get_sqs_request_headers(),
        }
    )
    context = RequestContext(request)
    context.account = "test"
    context.region = "us-west-1"
    context.service = sqs_service
    result = skeleton.invoke(context)

    # Use the parser from botocore to parse the serialized response
    response_parser = create_parser(sqs_service.protocol)
    parsed_response = response_parser.parse(
        result.to_readonly_response_dict(), sqs_service.operation_model("SendMessage").output_shape
    )

    # Test the ResponseMetadata
    assert "ResponseMetadata" in parsed_response
    assert "RequestId" in parsed_response["ResponseMetadata"]
    assert len(parsed_response["ResponseMetadata"]["RequestId"]) == 36
    assert "HTTPStatusCode" in parsed_response["ResponseMetadata"]
    assert parsed_response["ResponseMetadata"]["HTTPStatusCode"] == 501

    # Compare the (remaining) actual error payload
    assert "Error" in parsed_response
    assert parsed_response["Error"] == {
        "Code": "InternalFailure",
        "Message": oracle_message,
    }