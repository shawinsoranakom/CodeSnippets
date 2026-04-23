def create_rest_api(self, context: RequestContext, request: CreateRestApiRequest) -> RestApi:
        endpoint_configuration = request.get("endpointConfiguration", {})
        types = endpoint_configuration.get("types", [EndpointType.EDGE])
        ip_address_type = endpoint_configuration.get("ipAddressType")

        if not types:
            raise BadRequestException(
                "REGIONAL Configuration and EDGE Configuration cannot be both DISABLED."
            )
        elif len(types) > 1:
            raise BadRequestException("Cannot create an api with multiple Endpoint Types.")
        endpoint_type = types[0]

        error_messages = []
        if endpoint_type not in (EndpointType.PRIVATE, EndpointType.EDGE, EndpointType.REGIONAL):
            error_messages.append(
                f"Value '[{endpoint_type}]' at 'createRestApiInput.endpointConfiguration.types' failed to satisfy constraint: Member must satisfy constraint: [Member must satisfy enum value set: [PRIVATE, EDGE, REGIONAL]]",
            )
        elif not ip_address_type:
            if endpoint_type in (EndpointType.EDGE, EndpointType.REGIONAL):
                ip_address_type = IpAddressType.ipv4
            else:
                ip_address_type = IpAddressType.dualstack

        if ip_address_type not in (IpAddressType.ipv4, IpAddressType.dualstack, None):
            error_messages.append(
                f"Value '{ip_address_type}' at 'createRestApiInput.endpointConfiguration.ipAddressType' failed to satisfy constraint: Member must satisfy enum value set: [ipv4, dualstack]",
            )
        if error_messages:
            prefix = f"{len(error_messages)} validation error{'s' if len(error_messages) > 1 else ''} detected: "
            raise CommonServiceException(
                code="ValidationException",
                message=prefix + "; ".join(error_messages),
            )
        if request.get("description") == "":
            raise BadRequestException("Description cannot be an empty string")
        if types == [EndpointType.PRIVATE] and ip_address_type == IpAddressType.ipv4:
            raise BadRequestException("Only dualstack ipAddressType is supported for Private APIs.")

        minimum_compression_size = request.get("minimumCompressionSize")
        if minimum_compression_size is not None and (
            minimum_compression_size < 0 or minimum_compression_size > 10485760
        ):
            raise BadRequestException(
                "Invalid minimum compression size, must be between 0 and 10485760"
            )

        result = call_moto(context)
        rest_api = get_moto_rest_api(context, rest_api_id=result["id"])
        rest_api.version = request.get("version")
        if binary_media_types := request.get("binaryMediaTypes"):
            rest_api.binaryMediaTypes = binary_media_types

        response: RestApi = rest_api.to_dict()
        response["endpointConfiguration"]["ipAddressType"] = ip_address_type
        remove_empty_attributes_from_rest_api(response)
        store = get_apigateway_store(context=context)
        rest_api_container = RestApiContainer(rest_api=response)
        store.rest_apis[result["id"]] = rest_api_container
        # add the 2 default models
        rest_api_container.models[EMPTY_MODEL] = DEFAULT_EMPTY_MODEL
        rest_api_container.models[ERROR_MODEL] = DEFAULT_ERROR_MODEL

        return response