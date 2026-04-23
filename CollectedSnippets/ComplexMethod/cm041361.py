def _botocore_serializer_integration_test(
    *,
    service: str,
    action: str,
    response: dict,
    status_code: int = 200,
    expected_response_content: dict | None = None,
    protocol: str | None = None,
) -> dict:
    """
    Performs an integration test for the serializer using botocore as parser.
    It executes the following steps:
    - Load the given service (f.e. "sqs")
    - Serialize the response with the appropriate serializer from the AWS Service Framework
    - Parse the serialized response using the botocore parser
    - Checks if the metadata is correct (status code, requestID,...)
    - Checks if the parsed response content is equal to the input to the serializer

    :param service: to load the correct service specification, serializer, and parser
    :param action: to load the correct service specification, serializer, and parser
    :param response: which should be serialized and tested against
    :param status_code: Optional - expected status code of the response - defaults to 200
    :param expected_response_content: Optional - if the input data ("response") differs from the actually expected data
                                      (because f.e. it contains None values)
    :param: protocol: Optional: to specify which protocol to use for the service. If not provided,
                    fallback to the service's default protocol
    :return: boto-parsed serialized response
    """

    # Load the appropriate service
    service = load_service(service)
    service_protocol = protocol or service.protocol

    # Use our serializer to serialize the response
    response_serializer = create_serializer(service, protocol=service_protocol)
    # The serializer changes the incoming dict, therefore copy it before passing it to the serializer
    response_to_parse = copy.deepcopy(response)
    serialized_response = response_serializer.serialize_to_response(
        response_to_parse, service.operation_model(action), None, long_uid()
    )

    # Use the parser from botocore to parse the serialized response
    response_parser = create_parser(service_protocol)
    # Properly use HeadersDict from botocore to properly parse headers
    response_dict = serialized_response.to_readonly_response_dict()
    response_dict["headers"] = HeadersDict(response_dict.get("headers", {}))
    parsed_response = response_parser.parse(
        response_dict,
        service.operation_model(action).output_shape,
    )

    return_response = copy.deepcopy(parsed_response)

    # Check if the result is equal to the initial response params
    assert "ResponseMetadata" in parsed_response
    assert "HTTPStatusCode" in parsed_response["ResponseMetadata"]
    assert parsed_response["ResponseMetadata"]["HTTPStatusCode"] == status_code
    assert "RequestId" in parsed_response["ResponseMetadata"]
    assert len(parsed_response["ResponseMetadata"]["RequestId"]) == 36
    del parsed_response["ResponseMetadata"]

    if expected_response_content is None:
        expected_response_content = response
    if expected_response_content is not _skip_assert:
        assert parsed_response == expected_response_content

    return return_response