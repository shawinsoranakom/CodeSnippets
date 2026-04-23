def _retrieve_parameter_from_invocation_request(
        self,
        expr: str,
        invocation_request: InvocationRequest,
        case_sensitive_headers: dict[str, list[str]],
    ) -> str | list[str] | None:
        """
        See https://docs.aws.amazon.com/apigateway/latest/developerguide/request-response-data-mappings.html#mapping-response-parameters
        :param expr: mapping expression stripped from `method.request.`:
                     Can be of the following: `path.<param_name>`, `querystring.<param_name>`,
                     `multivaluequerystring.<param_name>`, `header.<param_name>`, `multivalueheader.<param_name>`,
                     `body` and `body.<JSONPath_expression>.`
        :param invocation_request: the InvocationRequest to map parameters from
        :return: the value to map in the RequestDataMapping
        """
        if expr.startswith("body"):
            body = invocation_request["body"] or b"{}"
            body = body.strip()
            try:
                decoded_body = self._json_load(body)
            except ValueError:
                raise BadRequestException(message="Invalid JSON in request body")

            if expr == "body":
                return to_str(body)

            elif expr.startswith("body."):
                json_path = expr.removeprefix("body.")
                return self._get_json_path_from_dict(decoded_body, json_path)
            else:
                LOG.warning(
                    "Unrecognized method.request parameter: '%s'. Skipping the parameter mapping.",
                    expr,
                )
                return None

        param_type, param_name = expr.split(".")
        if param_type == "path":
            return invocation_request["path_parameters"].get(param_name)

        elif param_type == "querystring":
            multi_qs_params = invocation_request["multi_value_query_string_parameters"].get(
                param_name
            )
            if multi_qs_params:
                return multi_qs_params[-1]

        elif param_type == "multivaluequerystring":
            multi_qs_params = invocation_request["multi_value_query_string_parameters"].get(
                param_name
            )
            if len(multi_qs_params) == 1:
                return multi_qs_params[0]
            return multi_qs_params

        elif param_type == "header":
            if header := case_sensitive_headers.get(param_name):
                return header[-1]

        elif param_type == "multivalueheader":
            if header := case_sensitive_headers.get(param_name):
                return ",".join(header)

        else:
            LOG.warning(
                "Unrecognized method.request parameter: '%s'. Skipping the parameter mapping.",
                expr,
            )