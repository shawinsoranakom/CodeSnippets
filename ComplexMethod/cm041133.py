def get_integration(
        self,
        context: RequestContext,
        rest_api_id: String,
        resource_id: String,
        http_method: String,
        **kwargs,
    ) -> Integration:
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

        response: Integration = call_moto(context)

        if integration_responses := response.get("integrationResponses"):
            for integration_response in integration_responses.values():
                remove_empty_attributes_from_integration_response(integration_response)

        if response.get("connectionType") == "VPC_LINK":
            # FIXME: this is hacky to workaround moto not saving the VPC Link `connectionId`
            # only do this internal check of Moto if the integration is of VPC_LINK type
            moto_rest_api = get_moto_rest_api(context=context, rest_api_id=rest_api_id)
            try:
                method = moto_rest_api.resources[resource_id].resource_methods[http_method]
                integration = method.method_integration
                if connection_id := getattr(integration, "connection_id", None):
                    response["connectionId"] = connection_id

            except (AttributeError, KeyError):
                # this error should have been caught by `call_moto`
                pass

        return response