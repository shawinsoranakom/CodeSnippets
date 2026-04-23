def _get_missing_required_parameters(method: Method, request: InvocationRequest) -> list[str]:
        missing_params = []
        if not (request_parameters := method.get("requestParameters")):
            return missing_params

        case_sensitive_headers = list(request.get("headers").keys())

        for request_parameter, required in sorted(request_parameters.items()):
            if not required:
                continue

            param_type, param_value = request_parameter.removeprefix("method.request.").split(".")
            match param_type:
                case "header":
                    is_missing = param_value not in case_sensitive_headers
                case "path":
                    path = request.get("path_parameters", "")
                    is_missing = param_value not in path
                case "querystring":
                    is_missing = param_value not in request.get("query_string_parameters", [])
                case _:
                    # This shouldn't happen
                    LOG.debug("Found an invalid request parameter: %s", request_parameter)
                    is_missing = False

            if is_missing:
                missing_params.append(param_value)

        return missing_params