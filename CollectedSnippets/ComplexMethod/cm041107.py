def import_api_from_openapi_spec(
    rest_api: MotoRestAPI, context: RequestContext, open_api_spec: dict, mode: PutMode
) -> tuple[MotoRestAPI, list[str]]:
    """Import an API from an OpenAPI spec document"""
    warnings = []

    # TODO There is an issue with the botocore specs so the parameters doesn't get populated as it should
    #  Once this is fixed we can uncomment the code below instead of taking the parameters the context request
    # query_params = request.get("parameters") or {}
    query_params: dict = context.request.values.to_dict()

    resolved_schema = resolve_references(copy.deepcopy(open_api_spec), rest_api_id=rest_api.id)
    account_id = context.account_id
    region_name = context.region

    # TODO:
    # 1. properly apply the mode (overwrite or merge)
    #    for now, it only considers it for the binaryMediaTypes
    # 2. validate the document type, "swagger" or "openapi"

    rest_api.version = (
        str(version) if (version := resolved_schema.get("info", {}).get("version")) else None
    )
    # XXX for some reason this makes cf tests fail that's why is commented.
    # test_cfn_handle_serverless_api_resource
    # rest_api.name = resolved_schema.get("info", {}).get("title")
    rest_api.description = resolved_schema.get("info", {}).get("description")

    # authorizers map to avoid duplication
    authorizers = {}

    store = get_apigateway_store(context=context)
    rest_api_container = store.rest_apis[rest_api.id]

    def is_api_key_required(path_payload: dict) -> bool:
        # TODO: consolidate and refactor with `create_authorizer`, duplicate logic for now
        if not (security_schemes := path_payload.get("security")):
            return False

        for security_scheme in security_schemes:
            for security_scheme_name in security_scheme.keys():
                # $.securityDefinitions is Swagger 2.0
                # $.components.SecuritySchemes is OpenAPI 3.0
                security_definitions = resolved_schema.get(
                    "securityDefinitions"
                ) or resolved_schema.get("components", {}).get("securitySchemes", {})
                if security_scheme_name in security_definitions:
                    security_config = security_definitions.get(security_scheme_name)
                    if (
                        OpenAPIExt.AUTHORIZER not in security_config
                        and security_config.get("type") == "apiKey"
                        and security_config.get("name", "").lower() == "x-api-key"
                    ):
                        return True
        return False

    def create_authorizers(security_schemes: dict) -> None:
        for security_scheme_name, security_config in security_schemes.items():
            aws_apigateway_authorizer = security_config.get(OpenAPIExt.AUTHORIZER, {})
            if not aws_apigateway_authorizer:
                continue

            if security_scheme_name in authorizers:
                continue

            authorizer_type = aws_apigateway_authorizer.get("type", "").upper()
            # TODO: do we need validation of resources here?
            authorizer = Authorizer(
                id=ApigwAuthorizerIdentifier(
                    account_id, region_name, security_scheme_name
                ).generate(),
                name=security_scheme_name,
                type=authorizer_type,
                authorizerResultTtlInSeconds=aws_apigateway_authorizer.get(
                    "authorizerResultTtlInSeconds", None
                ),
            )
            if provider_arns := aws_apigateway_authorizer.get("providerARNs"):
                authorizer["providerARNs"] = provider_arns
            if auth_type := security_config.get(OpenAPIExt.AUTHTYPE):
                authorizer["authType"] = auth_type
            if authorizer_uri := aws_apigateway_authorizer.get("authorizerUri"):
                authorizer["authorizerUri"] = authorizer_uri
            if authorizer_credentials := aws_apigateway_authorizer.get("authorizerCredentials"):
                authorizer["authorizerCredentials"] = authorizer_credentials
            if authorizer_type in ("TOKEN", "COGNITO_USER_POOLS"):
                header_name = security_config.get("name")
                authorizer["identitySource"] = f"method.request.header.{header_name}"
            elif identity_source := aws_apigateway_authorizer.get("identitySource"):
                # https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-swagger-extensions-authorizer.html
                # Applicable for the authorizer of the request and jwt type only
                authorizer["identitySource"] = identity_source
            if identity_validation_expression := aws_apigateway_authorizer.get(
                "identityValidationExpression"
            ):
                authorizer["identityValidationExpression"] = identity_validation_expression

            rest_api_container.authorizers[authorizer["id"]] = authorizer

            authorizers[security_scheme_name] = authorizer

    def get_authorizer(path_payload: dict) -> AuthorizerConfig | None:
        if not (security_schemes := path_payload.get("security")):
            return None

        for security_scheme in security_schemes:
            for security_scheme_name, scopes in security_scheme.items():
                if authorizer := authorizers.get(security_scheme_name):
                    return AuthorizerConfig(authorizer=authorizer, authorization_scopes=scopes)

    def get_or_create_path(abs_path: str, base_path: str):
        parts = abs_path.rstrip("/").replace("//", "/").split("/")
        parent_id = ""
        if len(parts) > 1:
            parent_path = "/".join(parts[:-1])
            parent = get_or_create_path(parent_path, base_path=base_path)
            parent_id = parent.id
        if existing := [
            r
            for r in rest_api.resources.values()
            if r.path_part == (parts[-1] or "/") and (r.parent_id or "") == (parent_id or "")
        ]:
            return existing[0]

        # construct relative path (without base path), then add field resources for this path
        rel_path = abs_path.removeprefix(base_path)
        return add_path_methods(rel_path, parts, parent_id=parent_id)

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

    def create_method_resource(child, method, method_schema):
        authorization_type = "NONE"
        api_key_required = is_api_key_required(method_schema)
        kwargs = {}

        if authorizer := get_authorizer(method_schema) or default_authorizer:
            method_authorizer = authorizer["authorizer"]
            # override the authorizer_type if it's a TOKEN or REQUEST to CUSTOM
            if (authorizer_type := method_authorizer["type"]) in ("TOKEN", "REQUEST"):
                authorization_type = "CUSTOM"
            else:
                authorization_type = authorizer_type

            kwargs["authorizer_id"] = method_authorizer["id"]

            if authorization_scopes := authorizer.get("authorization_scopes"):
                kwargs["authorization_scopes"] = authorization_scopes

        return child.add_method(
            method,
            api_key_required=api_key_required,
            authorization_type=authorization_type,
            operation_name=method_schema.get("operationId"),
            **kwargs,
        )

    models = resolved_schema.get("definitions") or resolved_schema.get("components", {}).get(
        "schemas", {}
    )
    for name, model_data in models.items():
        model_id = short_uid()[:6]  # length 6 to make TF tests pass
        model = Model(
            id=model_id,
            name=name,
            contentType=APPLICATION_JSON,
            description=model_data.get("description"),
            schema=json.dumps(model_data),
        )
        store.rest_apis[rest_api.id].models[name] = model

    # create the RequestValidators defined at the top-level field `x-amazon-apigateway-request-validators`
    request_validators = resolved_schema.get(OpenAPIExt.REQUEST_VALIDATORS, {})
    request_validator_name_id_map = {}
    for validator_name, validator_schema in request_validators.items():
        validator_id = short_uid()[:6]

        validator = RequestValidator(
            id=validator_id,
            name=validator_name,
            validateRequestBody=validator_schema.get("validateRequestBody") or False,
            validateRequestParameters=validator_schema.get("validateRequestParameters") or False,
        )

        store.rest_apis[rest_api.id].validators[validator_id] = validator
        request_validator_name_id_map[validator_name] = validator_id

    # get default requestValidator if present
    default_req_validator_name = resolved_schema.get(OpenAPIExt.REQUEST_VALIDATOR)

    # $.securityDefinitions is Swagger 2.0
    # $.components.SecuritySchemes is OpenAPI 3.0
    security_data = resolved_schema.get("securityDefinitions") or resolved_schema.get(
        "components", {}
    ).get("securitySchemes", {})
    # create the defined authorizers, even if they're not used by any routes
    if security_data:
        create_authorizers(security_data)

    # create default authorizer if present
    default_authorizer = get_authorizer(resolved_schema)

    # determine base path
    # default basepath mode is "ignore"
    # see https://docs.aws.amazon.com/apigateway/latest/developerguide/api-gateway-import-api-basePath.html
    basepath_mode = query_params.get("basepath") or "ignore"
    base_path = ""

    if basepath_mode != "ignore":
        # in Swagger 2.0, the basePath is a top-level property
        if "basePath" in resolved_schema:
            base_path = resolved_schema["basePath"]

        # in OpenAPI 3.0, the basePath is contained in the server object
        elif "servers" in resolved_schema:
            servers_property = resolved_schema.get("servers", [])
            for server in servers_property:
                # first, we check if there are a basePath variable (1st choice)
                if "basePath" in server.get("variables", {}):
                    base_path = server["variables"]["basePath"].get("default", "")
                    break
                # TODO: this allows both absolute and relative part, but AWS might not manage relative
                url_path = urlparse.urlparse(server.get("url", "")).path
                if url_path:
                    base_path = url_path if url_path != "/" else ""
                    break

    if basepath_mode == "split":
        base_path = base_path.strip("/").partition("/")[-1]
        base_path = f"/{base_path}" if base_path else ""

    api_paths = resolved_schema.get("paths", {})
    if api_paths:
        # Remove default root, then add paths from API spec
        # TODO: the default mode is now `merge`, not `overwrite` if using `PutRestApi`
        # TODO: quick hack for now, but do not remove the rootResource if the OpenAPI file is empty
        rest_api.resources = {}

    for path in api_paths:
        get_or_create_path(base_path + path, base_path=base_path)

    # binary types
    if mode == "merge":
        existing_binary_media_types = rest_api.binaryMediaTypes or []
    else:
        existing_binary_media_types = []

    rest_api.binaryMediaTypes = existing_binary_media_types + resolved_schema.get(
        OpenAPIExt.BINARY_MEDIA_TYPES, []
    )

    policy = resolved_schema.get(OpenAPIExt.POLICY)
    if policy:
        policy = json.dumps(policy) if isinstance(policy, dict) else str(policy)
        rest_api.policy = policy
    minimum_compression_size = resolved_schema.get(OpenAPIExt.MINIMUM_COMPRESSION_SIZE)
    if minimum_compression_size is not None:
        rest_api.minimum_compression_size = int(minimum_compression_size)
    endpoint_config = resolved_schema.get(OpenAPIExt.ENDPOINT_CONFIGURATION)
    if endpoint_config:
        if endpoint_config.get("vpcEndpointIds"):
            endpoint_config.setdefault("types", ["PRIVATE"])
        rest_api.endpoint_configuration = endpoint_config

    api_key_source = resolved_schema.get(OpenAPIExt.API_KEY_SOURCE)
    if api_key_source is not None:
        rest_api.api_key_source = api_key_source.upper()

    documentation = resolved_schema.get(OpenAPIExt.DOCUMENTATION)
    if documentation:
        add_documentation_parts(rest_api_container, documentation)

    return rest_api, warnings