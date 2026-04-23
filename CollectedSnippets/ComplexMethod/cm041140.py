def update_gateway_response(
        self,
        context: RequestContext,
        rest_api_id: String,
        response_type: GatewayResponseType,
        patch_operations: ListOfPatchOperation = None,
        **kwargs,
    ) -> GatewayResponse:
        """
        Support operations table:
         Path                | op:add        | op:replace | op:remove     | op:copy
         /statusCode         | Not supported | Supported  | Not supported | Not supported
         /responseParameters | Supported     | Supported  | Supported     | Not supported
         /responseTemplates  | Supported     | Supported  | Supported     | Not supported
        See https://docs.aws.amazon.com/apigateway/latest/api/patch-operations.html#UpdateGatewayResponse-Patch
        """
        store = get_apigateway_store(context=context)
        if not (rest_api_container := store.rest_apis.get(rest_api_id)):
            raise NotFoundException(
                f"Invalid API identifier specified {context.account_id}:{rest_api_id}"
            )

        if response_type not in DEFAULT_GATEWAY_RESPONSES:
            raise CommonServiceException(
                code="ValidationException",
                message=f"1 validation error detected: Value '{response_type}' at 'responseType' failed to satisfy constraint: Member must satisfy enum value set: [{', '.join(DEFAULT_GATEWAY_RESPONSES)}]",
            )

        if response_type not in rest_api_container.gateway_responses:
            # deep copy to avoid in place mutation of the default response when update using JSON patch
            rest_api_container.gateway_responses[response_type] = copy.deepcopy(
                DEFAULT_GATEWAY_RESPONSES[response_type]
            )
            rest_api_container.gateway_responses[response_type]["defaultResponse"] = False

        patched_entity = rest_api_container.gateway_responses[response_type]

        for index, operation in enumerate(patch_operations):
            if (op := operation.get("op")) not in VALID_PATCH_OPERATIONS:
                raise CommonServiceException(
                    code="ValidationException",
                    message=f"1 validation error detected: Value '{op}' at 'updateGatewayResponseInput.patchOperations.{index + 1}.member.op' failed to satisfy constraint: Member must satisfy enum value set: [{', '.join(VALID_PATCH_OPERATIONS)}]",
                )

            path = operation.get("path", "null")
            if not any(
                path.startswith(s_path)
                for s_path in ("/statusCode", "/responseParameters", "/responseTemplates")
            ):
                raise BadRequestException(f"Invalid patch path {path}")

            if op in ("add", "remove") and path == "/statusCode":
                raise BadRequestException(f"Invalid patch path {path}")

            elif op in ("add", "replace"):
                for param_type in ("responseParameters", "responseTemplates"):
                    if path.startswith(f"/{param_type}"):
                        if op == "replace":
                            param = path.removeprefix(f"/{param_type}/")
                            param = param.replace("~1", "/")
                            if param not in patched_entity.get(param_type):
                                raise NotFoundException("Invalid parameter name specified")
                        if operation.get("value") is None:
                            raise BadRequestException(
                                f"Invalid null or empty value in {param_type}"
                            )

        patch_api_gateway_entity(patched_entity, patch_operations)

        return patched_entity