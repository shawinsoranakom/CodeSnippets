def update_integration_response(
        self,
        context: RequestContext,
        rest_api_id: String,
        resource_id: String,
        http_method: String,
        status_code: StatusCode,
        patch_operations: ListOfPatchOperation = None,
        **kwargs,
    ) -> IntegrationResponse:
        # XXX: THIS IS NOT A COMPLETE IMPLEMENTATION, just the minimum required to get tests going
        # TODO: validate patch operations

        moto_rest_api = get_moto_rest_api(context, rest_api_id)
        moto_resource = moto_rest_api.resources.get(resource_id)
        if not moto_resource:
            raise NotFoundException("Invalid Resource identifier specified")

        moto_method = moto_resource.resource_methods.get(http_method)
        if not moto_method:
            raise NotFoundException("Invalid Method identifier specified")

        integration_response = moto_method.method_integration.integration_responses.get(status_code)
        if not integration_response:
            raise NotFoundException("Invalid Integration Response identifier specified")

        for patch_operation in patch_operations:
            op = patch_operation.get("op")
            path = patch_operation.get("path")

            # for path "/responseTemplates/application~1json"
            if "/responseTemplates" in path:
                integration_response.response_templates = (
                    integration_response.response_templates or {}
                )
                value = patch_operation.get("value")
                if not isinstance(value, str):
                    raise BadRequestException(
                        f"Invalid patch value  '{value}' specified for op '{op}'. Must be a string"
                    )
                param = path.removeprefix("/responseTemplates/")
                param = param.replace("~1", "/")
                if op == "remove":
                    integration_response.response_templates.pop(param)
                elif op in ("add", "replace"):
                    integration_response.response_templates[param] = value

            elif "/contentHandling" in path and op == "replace":
                integration_response.content_handling = patch_operation.get("value")

            elif "/selectionPattern" in path and op == "replace":
                integration_response.selection_pattern = patch_operation.get("value")

        response: IntegrationResponse = integration_response.to_json()
        # in case it's empty, we still want to pass it on as ""
        # TODO: add a test case for this
        response["selectionPattern"] = integration_response.selection_pattern

        return response