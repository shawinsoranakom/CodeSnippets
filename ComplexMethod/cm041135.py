def get_integration_response(
        self,
        context: RequestContext,
        rest_api_id: String,
        resource_id: String,
        http_method: String,
        status_code: StatusCode,
        **kwargs,
    ) -> IntegrationResponse:
        if not re.fullmatch(r"[1-5]\d\d", status_code):
            raise CommonServiceException(
                code="ValidationException",
                message=f"1 validation error detected: Value '{status_code}' at 'statusCode' failed to "
                f"satisfy constraint: Member must satisfy regular expression pattern: [1-5]\\d\\d",
            )
        try:
            moto_rest_api = get_moto_rest_api(context, rest_api_id)
        except NotFoundException:
            raise NotFoundException("Invalid Resource identifier specified")

        if not (moto_resource := moto_rest_api.resources.get(resource_id)):
            raise NotFoundException("Invalid Resource identifier specified")

        if not (moto_method := moto_resource.resource_methods.get(http_method)):
            raise NotFoundException("Invalid Method identifier specified")

        if not moto_method.method_integration:
            raise NotFoundException("Invalid Integration identifier specified")
        if not (
            integration_responses := moto_method.method_integration.integration_responses
        ) or not (integration_response := integration_responses.get(status_code)):
            raise NotFoundException("Invalid Response status code specified")

        response: IntegrationResponse = call_moto(context)
        remove_empty_attributes_from_integration_response(response)
        # moto does not return selectionPattern is set to an empty string
        # TODO: fix upstream
        if (
            "selectionPattern" not in response
            and integration_response.selection_pattern is not None
        ):
            response["selectionPattern"] = integration_response.selection_pattern
        return response