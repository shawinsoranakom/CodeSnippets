def update_rest_api(
        self,
        context: RequestContext,
        rest_api_id: String,
        patch_operations: ListOfPatchOperation = None,
        **kwargs,
    ) -> RestApi:
        rest_api = get_moto_rest_api(context, rest_api_id)

        fixed_patch_ops = []
        binary_media_types_path = "/binaryMediaTypes"
        # TODO: validate a bit more patch operations
        for patch_op in patch_operations:
            if patch_op["op"] not in ("add", "remove", "move", "test", "replace", "copy"):
                raise CommonServiceException(
                    code="ValidationException",
                    message=f"1 validation error detected: Value '{patch_op['op']}' at 'updateRestApiInput.patchOperations.1.member.op' failed to satisfy constraint: Member must satisfy enum value set: [add, remove, move, test, replace, copy]",
                )
            patch_op_path = patch_op.get("path", "")
            # binaryMediaTypes has a specific way of being set
            # see https://docs.aws.amazon.com/apigateway/latest/api/API_PatchOperation.html
            # TODO: maybe implement a more generalized way if this happens anywhere else
            if patch_op_path.startswith(binary_media_types_path):
                if patch_op_path == binary_media_types_path:
                    raise BadRequestException(f"Invalid patch path {patch_op_path}")
                value = patch_op_path.rsplit("/", maxsplit=1)[-1]
                path_value = value.replace("~1", "/")
                patch_op["path"] = binary_media_types_path

                if patch_op["op"] == "add":
                    patch_op["value"] = path_value

                elif patch_op["op"] == "remove":
                    remove_index = rest_api.binaryMediaTypes.index(path_value)
                    patch_op["path"] = f"{binary_media_types_path}/{remove_index}"

                elif patch_op["op"] == "replace":
                    # AWS is behaving weirdly, and will actually remove/add instead of replacing in place
                    # it will put the replaced value last in the array
                    replace_index = rest_api.binaryMediaTypes.index(path_value)
                    fixed_patch_ops.append(
                        {"op": "remove", "path": f"{binary_media_types_path}/{replace_index}"}
                    )
                    patch_op["op"] = "add"

            elif patch_op_path == "/minimumCompressionSize":
                if patch_op["op"] != "replace":
                    raise BadRequestException(
                        "Invalid patch operation specified. Must be one of: [replace]"
                    )

                try:
                    # try to cast the value to integer if truthy, else reject
                    value = int(val) if (val := patch_op.get("value")) else None
                except ValueError:
                    raise BadRequestException(
                        "Invalid minimum compression size, must be between 0 and 10485760"
                    )

                if value is not None and (value < 0 or value > 10485760):
                    raise BadRequestException(
                        "Invalid minimum compression size, must be between 0 and 10485760"
                    )
                patch_op["value"] = value

            elif patch_op_path.startswith("/endpointConfiguration/types"):
                if patch_op["op"] != "replace":
                    raise BadRequestException(
                        "Invalid patch operation specified. Must be 'add'|'remove'|'replace'"
                    )
                if patch_op.get("value") not in (
                    EndpointType.REGIONAL,
                    EndpointType.EDGE,
                    EndpointType.PRIVATE,
                ):
                    raise BadRequestException(
                        "Invalid EndpointTypes specified. Valid options are REGIONAL,EDGE,PRIVATE"
                    )
                if patch_op.get("value") == EndpointType.PRIVATE:
                    fixed_patch_ops.append(patch_op)
                    patch_op = {
                        "op": "replace",
                        "path": "/endpointConfiguration/ipAddressType",
                        "value": IpAddressType.dualstack,
                    }
                    fixed_patch_ops.append(patch_op)
                    continue

            elif patch_op_path.startswith("/endpointConfiguration/ipAddressType"):
                if patch_op["op"] != "replace":
                    raise BadRequestException(
                        "Invalid patch operation specified. Must be one of: [replace]"
                    )
                if (ipAddressType := patch_op.get("value")) not in (
                    IpAddressType.ipv4,
                    IpAddressType.dualstack,
                ):
                    raise BadRequestException("ipAddressType must be either ipv4 or dualstack.")
                if (
                    rest_api.endpoint_configuration["types"] == [EndpointType.PRIVATE]
                    and ipAddressType == IpAddressType.ipv4
                ):
                    raise BadRequestException(
                        "Only dualstack ipAddressType is supported for Private APIs."
                    )

            fixed_patch_ops.append(patch_op)

        patch_api_gateway_entity(rest_api, fixed_patch_ops)

        # fix data types after patches have been applied
        endpoint_configs = rest_api.endpoint_configuration or {}
        if isinstance(endpoint_configs.get("vpcEndpointIds"), str):
            endpoint_configs["vpcEndpointIds"] = [endpoint_configs["vpcEndpointIds"]]

        # minimum_compression_size is a unique path as it's a nullable integer,
        # it would throw an error if it stays an empty string
        if rest_api.minimum_compression_size == "":
            rest_api.minimum_compression_size = None

        response = rest_api.to_dict()

        remove_empty_attributes_from_rest_api(response, remove_tags=False)
        store = get_apigateway_store(context=context)
        store.rest_apis[rest_api_id].rest_api = response
        return response