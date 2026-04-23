def requests_error_response_xml_signature_calculation(
    message,
    string_to_sign=None,
    signature=None,
    expires=None,
    code=400,
    code_string="AccessDenied",
    aws_access_token="temp",
):
    response = RequestsResponse()
    response_template = f"""<?xml version="1.0" encoding="UTF-8"?>
        <Error>
            <Code>{code_string}</Code>
            <Message>{message}</Message>
            <RequestId>{short_uid()}</RequestId>
            <HostId>{short_uid()}</HostId>
        </Error>"""

    parsed_response = xmltodict.parse(response_template)
    response.status_code = code

    if signature and string_to_sign or code_string == "SignatureDoesNotMatch":
        bytes_signature = binascii.hexlify(bytes(signature, encoding="utf-8"))
        parsed_response["Error"]["Code"] = code_string
        parsed_response["Error"]["AWSAccessKeyId"] = aws_access_token
        parsed_response["Error"]["StringToSign"] = string_to_sign
        parsed_response["Error"]["SignatureProvided"] = signature
        parsed_response["Error"]["StringToSignBytes"] = "{}".format(bytes_signature.decode("utf-8"))
        set_response_content(response, xmltodict.unparse(parsed_response))

    if expires and code_string == "AccessDenied":
        server_time = datetime.datetime.utcnow().isoformat()[:-4]
        expires_isoformat = datetime.datetime.fromtimestamp(int(expires)).isoformat()[:-4]
        parsed_response["Error"]["Code"] = code_string
        parsed_response["Error"]["Expires"] = f"{expires_isoformat}Z"
        parsed_response["Error"]["ServerTime"] = f"{server_time}Z"
        set_response_content(response, xmltodict.unparse(parsed_response))

    if not signature and not expires and code_string == "AccessDenied":
        set_response_content(response, xmltodict.unparse(parsed_response))

    if response._content:
        return response