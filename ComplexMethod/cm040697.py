def lambda_result_to_response(result: InvocationResult):
    response = Response()

    # Set default headers
    response.headers.update(
        {
            "Content-Type": "application/json",
            "Connection": "keep-alive",
            "x-amzn-requestid": result.request_id,
            "x-amzn-trace-id": long_uid(),  # TODO: get the proper trace id here
        }
    )

    original_payload = to_str(result.payload)
    try:
        parsed_result = json.loads(original_payload)
    except JSONDecodeError:
        # URL router must be able to parse a Streaming Response without necessary defining it in the URL Config
        # And if the body is a simple string, it should be returned without issues
        split_index = original_payload.find("\x00" * 8)
        if split_index == -1:
            parsed_result = {"body": original_payload}
        else:
            metadata = original_payload[:split_index]
            body_str = original_payload[split_index + 8 :]
            parsed_result = {**json.loads(metadata), "body": body_str}

    # patch to fix whitespaces
    # TODO: check if this is a downstream issue of invocation result serialization
    original_payload = json.dumps(parsed_result, separators=(",", ":"))

    if isinstance(parsed_result, str):
        # a string is a special case here and is returned as-is
        response.data = parsed_result

    elif isinstance(parsed_result, dict):
        # if it's a dict it might be a proper response
        if isinstance(parsed_result.get("headers"), dict):
            response.headers.update(parsed_result.get("headers"))
        if "statusCode" in parsed_result:
            response.status_code = int(parsed_result["statusCode"])
        if "body" not in parsed_result:
            # TODO: test if providing a status code but no body actually works
            response.data = original_payload
        elif isinstance(parsed_result.get("body"), dict):
            response.data = json.dumps(parsed_result.get("body"))
        elif parsed_result.get("isBase64Encoded", False):
            body_bytes = to_bytes(to_str(parsed_result.get("body", "")))
            decoded_body_bytes = base64.b64decode(body_bytes)
            response.data = decoded_body_bytes
        else:
            response.data = parsed_result.get("body")
    else:
        response.data = original_payload

    return response