def _is_lambda_response_valid(lambda_response: dict) -> bool:
        if not isinstance(lambda_response, dict):
            return False

        if not validate_sub_dict_of_typed_dict(LambdaProxyResponse, lambda_response):
            return False

        if (headers := lambda_response.get("headers")) is not None:
            if not isinstance(headers, dict):
                return False
            if any(not isinstance(header_value, (str, bool)) for header_value in headers.values()):
                return False

        if (multi_value_headers := lambda_response.get("multiValueHeaders")) is not None:
            if not isinstance(multi_value_headers, dict):
                return False
            if any(
                not isinstance(header_value, list) for header_value in multi_value_headers.values()
            ):
                return False

        if "statusCode" in lambda_response:
            try:
                int(lambda_response["statusCode"])
            except ValueError:
                return False

        # TODO: add more validations of the values' type
        return True