def _get_missing_required_parameters(self, resource) -> list[str]:
        missing_params = []
        if not (request_parameters := resource.get("requestParameters")):
            return missing_params

        for request_parameter, required in sorted(request_parameters.items()):
            if not required:
                continue

            param_type, param_value = request_parameter.removeprefix("method.request.").split(".")
            match param_type:
                case "header":
                    is_missing = param_value not in self.context.headers
                case "path":
                    is_missing = param_value not in self.context.resource_path
                case "querystring":
                    is_missing = param_value not in self.context.query_params()
                case _:
                    # TODO: method.request.body is not specified in the documentation, and requestModels should do it
                    # verify this
                    is_missing = False

            if is_missing:
                missing_params.append(param_value)

        return missing_params