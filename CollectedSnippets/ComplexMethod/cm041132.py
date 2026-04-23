def update_request_validator(
        self,
        context: RequestContext,
        rest_api_id: String,
        request_validator_id: String,
        patch_operations: ListOfPatchOperation = None,
        **kwargs,
    ) -> RequestValidator:
        # TODO: add validation
        store = get_apigateway_store(context=context)
        rest_api_container = store.rest_apis.get(rest_api_id)
        # TODO: validate the restAPI id to remove the conditional
        validator = (
            rest_api_container.validators.get(request_validator_id) if rest_api_container else None
        )

        if validator is None:
            raise NotFoundException(
                f"Validator {request_validator_id} for API Gateway {rest_api_id} not found"
            )

        for patch_operation in patch_operations:
            path = patch_operation.get("path")
            operation = patch_operation.get("op")
            if operation != "replace":
                raise BadRequestException(
                    f"Invalid patch path  '{path}' specified for op '{operation}'. "
                    f"Please choose supported operations"
                )
            if path not in ("/name", "/validateRequestBody", "/validateRequestParameters"):
                raise BadRequestException(
                    f"Invalid patch path  '{path}' specified for op 'replace'. "
                    f"Must be one of: [/name, /validateRequestParameters, /validateRequestBody]"
                )

            key = path[1:]
            value = patch_operation.get("value")
            if key == "name" and not value:
                raise BadRequestException("Request Validator name cannot be blank")

            elif key in ("validateRequestParameters", "validateRequestBody"):
                value = value and value.lower() == "true" or False

            rest_api_container.validators[request_validator_id][key] = value

        return to_validator_response_json(
            rest_api_id, rest_api_container.validators[request_validator_id]
        )