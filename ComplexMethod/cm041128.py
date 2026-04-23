def update_method_response(
        self,
        context: RequestContext,
        rest_api_id: String,
        resource_id: String,
        http_method: String,
        status_code: StatusCode,
        patch_operations: ListOfPatchOperation | None = None,
        **kwargs,
    ) -> MethodResponse:
        error_messages = []
        for index, operation in enumerate(patch_operations):
            op = operation.get("op")
            if op not in VALID_PATCH_OPERATIONS:
                error_messages.append(
                    f"Value '{op}' at 'updateMethodResponseInput.patchOperations.{index + 1}.member.op' "
                    f"failed to satisfy constraint: Member must satisfy enum value set: [{', '.join(VALID_PATCH_OPERATIONS)}]"
                )

        if not re.fullmatch(r"[1-5]\d\d", status_code):
            error_messages.append(
                f"Value '{status_code}' at 'statusCode' failed to satisfy constraint: "
                "Member must satisfy regular expression pattern: [1-5]\\d\\d"
            )

        if error_messages:
            prefix = f"{len(error_messages)} validation error{'s' if len(error_messages) > 1 else ''} detected: "
            raise CommonServiceException(
                code="ValidationException",
                message=prefix + "; ".join(error_messages),
            )

        moto_rest_api = get_moto_rest_api(context, rest_api_id)
        moto_resource = moto_rest_api.resources.get(resource_id)
        if not moto_resource:
            raise NotFoundException("Invalid Resource identifier specified")

        moto_method = moto_resource.resource_methods.get(http_method)
        if not moto_method:
            raise NotFoundException("Invalid Method identifier specified")

        method_response = moto_method.method_responses.get(status_code)
        if not method_response:
            raise NotFoundException("Invalid Response status code specified")

        if method_response.response_models is None:
            method_response.response_models = {}
        if method_response.response_parameters is None:
            method_response.response_parameters = {}

        for patch_operation in patch_operations:
            op = patch_operation["op"]
            path = patch_operation["path"]
            value = patch_operation.get("value")

            if path.startswith("/responseParameters/"):
                param_name = path.removeprefix("/responseParameters/")
                if param_name not in method_response.response_parameters and op in (
                    "replace",
                    "remove",
                ):
                    raise NotFoundException("Invalid parameter name specified")
                if op in ("add", "replace"):
                    method_response.response_parameters[param_name] = value == "true"
                elif op == "remove":
                    method_response.response_parameters.pop(param_name)

            elif path.startswith("/responseModels/"):
                param_name = path.removeprefix("/responseModels/")
                param_name = param_name.replace("~1", "/")
                if param_name not in method_response.response_models and op in (
                    "replace",
                    "remove",
                ):
                    raise NotFoundException("Content-Type specified was not found")
                if op in ("add", "replace"):
                    method_response.response_models[param_name] = value
                elif op == "remove":
                    method_response.response_models.pop(param_name)
            else:
                raise BadRequestException(f"Invalid patch path {path}")

        response: MethodResponse = method_response.to_json()

        # AWS doesn't send back empty responseParameters or responseModels
        if not method_response.response_parameters:
            response.pop("responseParameters")
        if not method_response.response_models:
            response.pop("responseModels")

        return response