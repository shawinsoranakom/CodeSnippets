def _botocore_error_serializer_integration_test(
    service_model_name: str,
    action: str,
    exception: ServiceException,
    code: str,
    status_code: int,
    message: str | None,
    is_sender_fault: bool = False,
    protocol: str | None = None,
    **additional_error_fields: Any,
) -> dict:
    """
    Performs an integration test for the error serialization using botocore as parser.
    It executes the following steps:
    - Load the given service (f.e. "sqs")
    - Serialize the _error_ response with the appropriate serializer from the AWS Serivce Framework
    - Parse the serialized error response using the botocore parser
    - Checks if the metadata is correct (status code, requestID,...)
    - Checks if the parsed error response content is correct

    :param service_model_name: to load the correct service specification, serializer, and parser
    :param action: to load the correct service specification, serializer, and parser
    :param exception: which should be serialized and tested against
    :param code: expected "code" of the exception (i.e. the AWS specific exception ID, f.e.
                 "CloudFrontOriginAccessIdentityAlreadyExists")
    :param status_code: expected HTTP response status code
    :param message: expected error message
    :param is_sender_fault: expected fault type is sender
    :param additional_error_fields: additional fields which need to be present (for exception shapes with members)
    :return: boto-parsed serialized error response
    """

    # Load the appropriate service
    service = load_service(service_model_name)
    service_protocol = protocol or service.protocol

    # Use our serializer to serialize the response
    response_serializer = create_serializer(service, service_protocol)
    serialized_response = response_serializer.serialize_error_to_response(
        exception, service.operation_model(action), {}, long_uid()
    )

    # Use the parser from botocore to parse the serialized response
    response_dict = serialized_response.to_readonly_response_dict()

    # botocore converts the headers to lower-case keys
    # f.e. needed for x-amzn-errortype
    response_dict["headers"] = HeadersDict(response_dict["headers"])

    response_parser: ResponseParser = create_parser(service_protocol)
    parsed_response = response_parser.parse(
        response_dict,
        service.operation_model(action).output_shape,
    )
    # Add the modeled error shapes
    error_shape = service.shape_for_error_code(exception.code)
    modeled_parse = response_parser.parse(response_dict, error_shape)
    parsed_response.update(modeled_parse)

    # Check if the result is equal to the initial response params
    assert "Error" in parsed_response
    assert "Code" in parsed_response["Error"]
    assert "Message" in parsed_response["Error"]
    assert parsed_response["Error"]["Code"] == code
    assert parsed_response["Error"]["Message"] == message

    assert "ResponseMetadata" in parsed_response
    assert "RequestId" in parsed_response["ResponseMetadata"]
    assert len(parsed_response["ResponseMetadata"]["RequestId"]) == 36
    assert "HTTPStatusCode" in parsed_response["ResponseMetadata"]
    assert parsed_response["ResponseMetadata"]["HTTPStatusCode"] == status_code
    type = parsed_response["Error"].get("Type")
    if is_sender_fault:
        assert type == "Sender"
    elif service_protocol == "smithy-rpc-v2-cbor" and service.is_query_compatible:
        assert type == "Receiver"
    else:
        assert type is None
    if additional_error_fields:
        for key, value in additional_error_fields.items():
            assert key in parsed_response
            assert parsed_response[key] == value
    return parsed_response