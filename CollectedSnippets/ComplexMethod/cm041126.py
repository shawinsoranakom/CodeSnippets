def put_method(
        self,
        context: RequestContext,
        rest_api_id: String,
        resource_id: String,
        http_method: String,
        authorization_type: String,
        authorizer_id: String = None,
        api_key_required: Boolean = None,
        operation_name: String = None,
        request_parameters: MapOfStringToBoolean = None,
        request_models: MapOfStringToString = None,
        request_validator_id: String = None,
        authorization_scopes: ListOfString = None,
        **kwargs,
    ) -> Method:
        # TODO: add missing validation? check order of validation as well
        moto_backend = get_moto_backend(context.account_id, context.region)
        moto_rest_api: MotoRestAPI = moto_backend.apis.get(rest_api_id)
        if not moto_rest_api or not (moto_resource := moto_rest_api.resources.get(resource_id)):
            raise NotFoundException("Invalid Resource identifier specified")

        if http_method not in ("GET", "PUT", "POST", "DELETE", "PATCH", "OPTIONS", "HEAD", "ANY"):
            raise BadRequestException(
                "Invalid HttpMethod specified. "
                "Valid options are GET,PUT,POST,DELETE,PATCH,OPTIONS,HEAD,ANY"
            )

        if request_parameters:
            request_parameters_names = {
                name.rsplit(".", maxsplit=1)[-1] for name in request_parameters.keys()
            }
            if len(request_parameters_names) != len(request_parameters):
                raise BadRequestException(
                    "Parameter names must be unique across querystring, header and path"
                )
        need_authorizer_id = authorization_type in ("CUSTOM", "COGNITO_USER_POOLS")
        store = get_apigateway_store(context=context)
        rest_api_container = store.rest_apis[rest_api_id]
        if need_authorizer_id and (
            not authorizer_id or authorizer_id not in rest_api_container.authorizers
        ):
            # TODO: will be cleaner with https://github.com/localstack/localstack/pull/7750
            raise BadRequestException(
                "Invalid authorizer ID specified. "
                "Setting the authorization type to CUSTOM or COGNITO_USER_POOLS requires a valid authorizer."
            )

        if request_validator_id and request_validator_id not in rest_api_container.validators:
            raise BadRequestException("Invalid Request Validator identifier specified")

        if request_models:
            for content_type, model_name in request_models.items():
                # FIXME: add Empty model to rest api at creation
                if model_name == EMPTY_MODEL:
                    continue
                if model_name not in rest_api_container.models:
                    raise BadRequestException(f"Invalid model identifier specified: {model_name}")

        response: Method = call_moto(context)
        remove_empty_attributes_from_method(response)
        moto_http_method = moto_resource.resource_methods[http_method]
        moto_http_method.authorization_type = moto_http_method.authorization_type.upper()

        # this is straight from the moto patch, did not test it yet but has the same functionality
        # FIXME: check if still necessary after testing Authorizers
        if need_authorizer_id and "authorizerId" not in response:
            response["authorizerId"] = authorizer_id

        response["authorizationType"] = response["authorizationType"].upper()

        return response