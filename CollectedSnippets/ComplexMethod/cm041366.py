def _botocore_parser_integration_test(
    *,
    service: str,
    action: str,
    protocol: str = None,
    headers: dict = None,
    expected: dict = None,
    **kwargs,
):
    # Load the appropriate service
    service = load_service(service)
    service_protocol = protocol or service.protocol
    # Use the serializer from botocore to serialize the request params
    serializer = create_serializer(service_protocol)

    operation_model = service.operation_model(action)
    serialized_request = serializer.serialize_to_request(kwargs, operation_model)

    # botocore >= 1.28 might modify the url path of the request dict (specifically for S3).
    # It will then set the original url path as "auth_path". If the auth_path is set, we reset the url_path.
    # Since botocore 1.31.2, botocore will strip the query from the `authPart`
    # We need to add it back from `requestUri` field
    if auth_path := serialized_request.get("auth_path"):
        path, sep, query = serialized_request["url_path"].partition("?")
        serialized_request["url_path"] = f"{auth_path}{sep}{query}"

    prepare_request_dict(serialized_request, "")
    split_url = urlsplit(serialized_request.get("url"))
    path = split_url.path
    query_string = split_url.query
    body = serialized_request["body"]
    # use custom headers (if provided), or headers from serialized request as default
    headers = serialized_request.get("headers") if headers is None else headers

    if service_protocol in ["query", "ec2"]:
        # Serialize the body as query parameter
        body = urlencode(serialized_request["body"])

    # Use our parser to parse the serialized body
    parser = create_parser(service, service_protocol)
    parsed_operation_model, parsed_request = parser.parse(
        HttpRequest(
            method=serialized_request.get("method") or "GET",
            path=unquote(path),
            query_string=to_str(query_string),
            headers=headers,
            body=body,
            raw_path=path,
        )
    )

    # Check if the determined operation_model is correct
    assert parsed_operation_model == operation_model

    # Check if the result is equal to the given "expected" dict or the kwargs (if "expected" has not been set)
    expected = expected or kwargs
    # The parser adds None for none-existing members on purpose. Remove those for the assert
    expected = {key: value for key, value in expected.items() if value is not None}
    parsed_request = {key: value for key, value in parsed_request.items() if value is not None}
    assert parsed_request == expected