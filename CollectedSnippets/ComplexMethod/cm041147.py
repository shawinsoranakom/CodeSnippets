def lambda_result_to_response(cls, result) -> LambdaResponse:
        response = LambdaResponse()
        response.headers.update({"content-type": "application/json"})
        parsed_result = result if isinstance(result, dict) else json.loads(str(result or "{}"))
        parsed_result = common.json_safe(parsed_result)
        parsed_result = {} if parsed_result is None else parsed_result

        if set(parsed_result) - {
            "body",
            "statusCode",
            "headers",
            "isBase64Encoded",
            "multiValueHeaders",
        }:
            LOG.warning(
                'Lambda output should follow the next JSON format: { "isBase64Encoded": true|false, "statusCode": httpStatusCode, "headers": { "headerName": "headerValue", ... },"body": "..."}\n Lambda output: %s',
                parsed_result,
            )
            response.status_code = 502
            response._content = json.dumps({"message": "Internal server error"})
            return response

        response.status_code = int(parsed_result.get("statusCode", 200))
        parsed_headers = parsed_result.get("headers", {})
        if parsed_headers is not None:
            response.headers.update(parsed_headers)
        try:
            result_body = parsed_result.get("body")
            if isinstance(result_body, dict):
                response._content = json.dumps(result_body)
            else:
                body_bytes = to_bytes(to_str(result_body or ""))
                if parsed_result.get("isBase64Encoded", False):
                    body_bytes = base64.b64decode(body_bytes)
                response._content = body_bytes
        except Exception as e:
            LOG.warning("Couldn't set Lambda response content: %s", e)
            response._content = "{}"
        response.multi_value_headers = parsed_result.get("multiValueHeaders") or {}
        return response