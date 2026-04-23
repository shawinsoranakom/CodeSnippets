def _retrieve_parameter_from_integration_response(
        self,
        expr: str,
        integration_response: EndpointResponse,
        case_sensitive_headers: dict[str, list[str]],
    ) -> str | None:
        """
        See https://docs.aws.amazon.com/apigateway/latest/developerguide/request-response-data-mappings.html#mapping-response-parameters
        :param expr: mapping expression stripped from `integration.response.`:
                     Can be of the following: `header.<param_name>`, multivalueheader.<param_name>, `body` and
                     `body.<JSONPath_expression>.`
        :param integration_response: the Response to map parameters from
        :return: the value to map in the ResponseDataMapping
        """
        if expr.startswith("body"):
            body = integration_response.get("body") or b"{}"
            body = body.strip()
            try:
                decoded_body = self._json_load(body)
            except ValueError:
                raise InternalFailureException(message="Internal server error")

            if expr == "body":
                return to_str(body)

            elif expr.startswith("body."):
                json_path = expr.removeprefix("body.")
                return self._get_json_path_from_dict(decoded_body, json_path)
            else:
                LOG.warning(
                    "Unrecognized integration.response parameter: '%s'. Skipping the parameter mapping.",
                    expr,
                )
                return None

        param_type, param_name = expr.split(".")

        if param_type == "header":
            if header := case_sensitive_headers.get(param_name):
                return header[-1]

        elif param_type == "multivalueheader":
            if header := case_sensitive_headers.get(param_name):
                return ",".join(header)

        else:
            LOG.warning(
                "Unrecognized integration.response parameter: '%s'. Skipping the parameter mapping.",
                expr,
            )