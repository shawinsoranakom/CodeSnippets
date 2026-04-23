def add_path_methods(rel_path: str, parts: list[str], parent_id=""):
        rel_path = rel_path or "/"
        child_id = ApigwResourceIdentifier(account_id, region_name, parent_id, rel_path).generate()

        # Create a `Resource` for the passed `rel_path`
        resource = Resource(
            account_id=rest_api.account_id,
            resource_id=child_id,
            region_name=rest_api.region_name,
            api_id=rest_api.id,
            path_part=parts[-1] or "/",
            parent_id=parent_id,
        )

        paths_dict = resolved_schema["paths"]
        method_paths = paths_dict.get(rel_path, {})
        # Iterate over each field of the `path` to try to find the methods defined
        for field, field_schema in method_paths.items():
            if field in [
                "parameters",
                "servers",
                "description",
                "summary",
                "$ref",
            ] or not isinstance(field_schema, dict):
                LOG.warning("Ignoring unsupported field %s in path %s", field, rel_path)
                # TODO: check if we should skip parameters, those are global parameters applied to every routes but
                #  can be overridden at the operation level
                continue

            method_name = field.upper()
            if method_name == OpenAPIExt.ANY_METHOD.upper():
                method_name = "ANY"

            # Create the `Method` resource for each method path
            method_resource = create_method_resource(resource, method_name, field_schema)

            # Get the `Method` requestParameters and requestModels
            request_parameters_schema = field_schema.get("parameters", [])
            request_parameters = {}
            request_models = {}
            if request_parameters_schema:
                for req_param_data in request_parameters_schema:
                    # For Swagger 2.0, possible values for `in` from the specs are "query", "header", "path",
                    # "formData" or "body".
                    # For OpenAPI 3.0, values are "query", "header", "path" or "cookie".
                    # Only "path", "header" and "query" are supported in API Gateway for requestParameters
                    # "body" is mapped to a requestModel
                    param_location = req_param_data.get("in")
                    param_name = req_param_data.get("name")
                    param_required = req_param_data.get("required", False)
                    if param_location in ("query", "header", "path"):
                        if param_location == "query":
                            param_location = "querystring"

                        request_parameters[f"method.request.{param_location}.{param_name}"] = (
                            param_required
                        )

                    elif param_location == "body":
                        request_models = {APPLICATION_JSON: param_name}

                    else:
                        LOG.warning(
                            "Ignoring unsupported requestParameters/requestModels location value for %s: %s",
                            param_name,
                            param_location,
                        )
                        continue

            # this replaces 'body' in Parameters for OpenAPI 3.0, a requestBody Object
            # https://swagger.io/specification/v3/#request-body-object
            if request_models_schema := field_schema.get("requestBody"):
                model_ref = None
                for content_type, media_type in request_models_schema.get("content", {}).items():
                    # we're iterating over the Media Type object:
                    # https://swagger.io/specification/v3/#media-type-object
                    if content_type == APPLICATION_JSON:
                        model_ref = media_type.get("schema", {}).get("$ref")
                        continue
                    LOG.warning(
                        "Found '%s' content-type for the MethodResponse model for path '%s' and method '%s', not adding the model as currently not supported",
                        content_type,
                        rel_path,
                        method_name,
                    )
                if model_ref:
                    model_schema = model_ref.rsplit("/", maxsplit=1)[-1]
                    request_models = {APPLICATION_JSON: model_schema}

            method_resource.request_models = request_models or None

            # check if there's a request validator set in the method
            request_validator_name = field_schema.get(
                OpenAPIExt.REQUEST_VALIDATOR, default_req_validator_name
            )
            if request_validator_name:
                if not (
                    req_validator_id := request_validator_name_id_map.get(request_validator_name)
                ):
                    # Might raise an exception here if we properly validate the template
                    LOG.warning(
                        "A validator ('%s') was referenced for %s.(%s), but is not defined",
                        request_validator_name,
                        rel_path,
                        method_name,
                    )
                method_resource.request_validator_id = req_validator_id

            # we check if there's a path parameter, AWS adds the requestParameter automatically
            resource_path_part = parts[-1].strip("/")
            if is_variable_path(resource_path_part) and not is_greedy_path(resource_path_part):
                path_parameter = resource_path_part[1:-1]  # remove the curly braces
                request_parameters[f"method.request.path.{path_parameter}"] = True

            method_resource.request_parameters = request_parameters or None

            # Create the `MethodResponse` for the previously created `Method`
            method_responses = field_schema.get("responses", {})
            for method_status_code, method_response in method_responses.items():
                method_status_code = str(method_status_code)
                method_response_model = None
                model_ref = None
                # separating the two different versions, Swagger (2.0) and OpenAPI 3.0
                if "schema" in method_response:  # this is Swagger
                    model_ref = method_response["schema"].get("$ref")
                elif "content" in method_response:  # this is OpenAPI 3.0
                    for content_type, media_type in method_response["content"].items():
                        # we're iterating over the Media Type object:
                        # https://swagger.io/specification/v3/#media-type-object
                        if content_type == APPLICATION_JSON:
                            model_ref = media_type.get("schema", {}).get("$ref")
                            continue
                        LOG.warning(
                            "Found '%s' content-type for the MethodResponse model for path '%s' and method '%s', not adding the model as currently not supported",
                            content_type,
                            rel_path,
                            method_name,
                        )

                if model_ref:
                    model_schema = model_ref.rsplit("/", maxsplit=1)[-1]

                    method_response_model = {APPLICATION_JSON: model_schema}

                method_response_parameters = {}
                if response_param_headers := method_response.get("headers"):
                    for header, header_info in response_param_headers.items():
                        # TODO: make use of `header_info`
                        method_response_parameters[f"method.response.header.{header}"] = False

                method_resource.create_response(
                    method_status_code,
                    method_response_model,
                    method_response_parameters or None,
                )

            # Create the `Integration` for the previously created `Method`
            method_integration = field_schema.get(OpenAPIExt.INTEGRATION, {})

            integration_type = (
                i_type.upper() if (i_type := method_integration.get("type")) else None
            )

            match integration_type:
                case "AWS_PROXY":
                    # if the integration is AWS_PROXY with lambda, the only accepted integration method is POST
                    integration_method = "POST"
                case _:
                    integration_method = (
                        method_integration.get("httpMethod") or method_name
                    ).upper()

            connection_type = (
                ConnectionType.INTERNET
                if integration_type in (IntegrationType.HTTP, IntegrationType.HTTP_PROXY)
                else None
            )

            if integration_request_parameters := method_integration.get("requestParameters"):
                validated_parameters = {}
                for k, v in integration_request_parameters.items():
                    if isinstance(v, str):
                        validated_parameters[k] = v
                    else:
                        # TODO This fixes for boolean serialization. We should validate how other types behave
                        value = str(v).lower()
                        warnings.append(
                            "Invalid format for 'requestParameters'. Expected type string for property "
                            f"'{k}' of resource '{resource.get_path()}' and method '{method_name}' but got '{value}'"
                        )

                integration_request_parameters = validated_parameters

            integration = Integration(
                http_method=integration_method,
                uri=method_integration.get("uri"),
                integration_type=integration_type,
                passthrough_behavior=method_integration.get(
                    "passthroughBehavior", "WHEN_NO_MATCH"
                ).upper(),
                request_templates=method_integration.get("requestTemplates"),
                request_parameters=integration_request_parameters,
                cache_namespace=resource.id,
                timeout_in_millis=method_integration.get("timeoutInMillis") or "29000",
                content_handling=method_integration.get("contentHandling"),
                connection_type=connection_type,
            )

            # Create the `IntegrationResponse` for the previously created `Integration`
            if method_integration_responses := method_integration.get("responses"):
                for pattern, integration_responses in method_integration_responses.items():
                    integration_response_templates = integration_responses.get("responseTemplates")
                    integration_response_parameters = integration_responses.get(
                        "responseParameters"
                    )

                    integration_response = integration.create_integration_response(
                        status_code=str(integration_responses.get("statusCode", 200)),
                        selection_pattern=pattern if pattern != "default" else None,
                        response_templates=integration_response_templates,
                        response_parameters=integration_response_parameters,
                        content_handling=None,
                    )
                    # moto set the responseTemplates to an empty dict when it should be None if not defined
                    if integration_response_templates is None:
                        integration_response.response_templates = None

            resource.resource_methods[method_name].method_integration = integration

        rest_api.resources[child_id] = resource
        rest_api_container.resource_children.setdefault(parent_id, []).append(child_id)
        return resource