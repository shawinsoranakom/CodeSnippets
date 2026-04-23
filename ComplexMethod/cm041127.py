def update_method(
        self,
        context: RequestContext,
        rest_api_id: String,
        resource_id: String,
        http_method: String,
        patch_operations: ListOfPatchOperation = None,
        **kwargs,
    ) -> Method:
        # see https://www.linkedin.com/pulse/updating-aws-cli-patch-operations-rest-api-yitzchak-meirovich/
        # for path construction
        moto_backend = get_moto_backend(context.account_id, context.region)
        moto_rest_api: MotoRestAPI = moto_backend.apis.get(rest_api_id)
        if not moto_rest_api or not (moto_resource := moto_rest_api.resources.get(resource_id)):
            raise NotFoundException("Invalid Resource identifier specified")

        if not (moto_method := moto_resource.resource_methods.get(http_method)):
            raise NotFoundException("Invalid Method identifier specified")
        store = get_apigateway_store(context=context)
        rest_api = store.rest_apis[rest_api_id]
        applicable_patch_operations = []
        modifying_auth_type = False
        modified_authorizer_id = False
        had_req_params = bool(moto_method.request_parameters)
        had_req_models = bool(moto_method.request_models)

        for patch_operation in patch_operations:
            op = patch_operation.get("op")
            path = patch_operation.get("path")
            # if the path is not supported at all, raise an Exception
            if len(path.split("/")) > 3 or not any(
                path.startswith(s_path) for s_path in UPDATE_METHOD_PATCH_PATHS["supported_paths"]
            ):
                raise BadRequestException(f"Invalid patch path {path}")

            # if the path is not supported by the operation, ignore it and skip
            op_supported_path = UPDATE_METHOD_PATCH_PATHS.get(op, [])
            if not any(path.startswith(s_path) for s_path in op_supported_path):
                available_ops = [
                    available_op
                    for available_op in ("add", "replace", "delete")
                    if available_op != op
                ]
                supported_ops = ", ".join(
                    [
                        supported_op
                        for supported_op in available_ops
                        if any(
                            path.startswith(s_path)
                            for s_path in UPDATE_METHOD_PATCH_PATHS.get(supported_op, [])
                        )
                    ]
                )
                raise BadRequestException(
                    f"Invalid patch operation specified. Must be one of: [{supported_ops}]"
                )

            value = patch_operation.get("value")
            if op not in ("add", "replace"):
                # skip
                applicable_patch_operations.append(patch_operation)
                continue

            if path == "/authorizationType" and value in ("CUSTOM", "COGNITO_USER_POOLS"):
                modifying_auth_type = True

            elif path == "/authorizerId":
                modified_authorizer_id = value

            if any(
                path.startswith(s_path) for s_path in ("/apiKeyRequired", "/requestParameters/")
            ):
                patch_op = {"op": op, "path": path, "value": str_to_bool(value)}
                applicable_patch_operations.append(patch_op)
                continue

            elif path == "/requestValidatorId" and value not in rest_api.validators:
                if not value:
                    # you can remove a requestValidator by passing an empty string as a value
                    patch_op = {"op": "remove", "path": path, "value": value}
                    applicable_patch_operations.append(patch_op)
                    continue
                raise BadRequestException("Invalid Request Validator identifier specified")

            elif path.startswith("/requestModels/"):
                if value != EMPTY_MODEL and value not in rest_api.models:
                    raise BadRequestException(f"Invalid model identifier specified: {value}")

            applicable_patch_operations.append(patch_operation)

        if modifying_auth_type:
            if not modified_authorizer_id or modified_authorizer_id not in rest_api.authorizers:
                raise BadRequestException(
                    "Invalid authorizer ID specified. "
                    "Setting the authorization type to CUSTOM or COGNITO_USER_POOLS requires a valid authorizer."
                )
        elif modified_authorizer_id:
            if moto_method.authorization_type not in ("CUSTOM", "COGNITO_USER_POOLS"):
                # AWS will ignore this patch if the method does not have a proper authorization type
                # filter the patches to remove the modified authorizerId
                applicable_patch_operations = [
                    op for op in applicable_patch_operations if op.get("path") != "/authorizerId"
                ]

        # TODO: test with multiple patch operations which would not be compatible between each other
        patch_api_gateway_entity(moto_method, applicable_patch_operations)

        # if we removed all values of those fields, set them to None so that they're not returned anymore
        if had_req_params and len(moto_method.request_parameters) == 0:
            moto_method.request_parameters = None
        if had_req_models and len(moto_method.request_models) == 0:
            moto_method.request_models = None

        response = moto_method.to_json()
        remove_empty_attributes_from_method(response)
        remove_empty_attributes_from_integration(response.get("methodIntegration"))
        return response