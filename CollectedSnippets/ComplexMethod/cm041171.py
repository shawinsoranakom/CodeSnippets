def parse_lambda_response(self, payload: bytes) -> LambdaProxyResponse:
        try:
            lambda_response = json.loads(payload)
        except json.JSONDecodeError:
            LOG.warning(
                'Lambda output should follow the next JSON format: { "isBase64Encoded": true|false, "statusCode": httpStatusCode, "headers": { "headerName": "headerValue", ... },"body": "..."} but was: %s',
                payload,
            )
            LOG.debug(
                "Execution failed due to configuration error: Malformed Lambda proxy response"
            )
            raise InternalServerError("Internal server error", status_code=502)

        # none of the lambda response fields are mandatory, but you cannot return any other fields
        if not self._is_lambda_response_valid(lambda_response):
            if "errorMessage" in lambda_response:
                LOG.debug(
                    "Lambda execution failed with status 200 due to customer function error: %s. Lambda request id: %s",
                    lambda_response["errorMessage"],
                    lambda_response.get("requestId", "<Unknown Request Id>"),
                )
            else:
                LOG.warning(
                    'Lambda output should follow the next JSON format: { "isBase64Encoded": true|false, "statusCode": httpStatusCode, "headers": { "headerName": "headerValue", ... },"body": "..."} but was: %s',
                    payload,
                )
                LOG.debug(
                    "Execution failed due to configuration error: Malformed Lambda proxy response"
                )
            raise InternalServerError("Internal server error", status_code=502)

        def serialize_header(value: bool | str) -> str:
            if isinstance(value, bool):
                return "true" if value else "false"
            return value

        if headers := lambda_response.get("headers"):
            lambda_response["headers"] = {k: serialize_header(v) for k, v in headers.items()}

        if multi_value_headers := lambda_response.get("multiValueHeaders"):
            lambda_response["multiValueHeaders"] = {
                k: [serialize_header(v) for v in values]
                for k, values in multi_value_headers.items()
            }

        return lambda_response