def put_integration(
        self, context: RequestContext, request: PutIntegrationRequest, **kwargs
    ) -> Integration:
        if (integration_type := request.get("type")) not in VALID_INTEGRATION_TYPES:
            raise CommonServiceException(
                "ValidationException",
                f"1 validation error detected: Value '{integration_type}' at "
                f"'putIntegrationInput.type' failed to satisfy constraint: "
                f"Member must satisfy enum value set: [HTTP, MOCK, AWS_PROXY, HTTP_PROXY, AWS]",
            )

        elif integration_type in (IntegrationType.AWS_PROXY, IntegrationType.AWS):
            if not request.get("integrationHttpMethod"):
                raise BadRequestException("Enumeration value for HttpMethod must be non-empty")
            if not (integration_uri := request.get("uri") or "").startswith("arn:"):
                raise BadRequestException("Invalid ARN specified in the request")

            try:
                parsed_arn = parse_arn(integration_uri)
            except InvalidArnException:
                raise BadRequestException("Invalid ARN specified in the request")

            if not any(
                parsed_arn["resource"].startswith(action_type) for action_type in ("path", "action")
            ):
                raise BadRequestException("AWS ARN for integration must contain path or action")

            if integration_type == IntegrationType.AWS_PROXY and (
                parsed_arn["account"] != "lambda"
                or not parsed_arn["resource"].startswith("path/2015-03-31/functions/")
            ):
                # the Firehose message is misleading, this is not implemented in AWS
                raise BadRequestException(
                    "Integrations of type 'AWS_PROXY' currently only supports "
                    "Lambda function and Firehose stream invocations."
                )

        moto_rest_api = get_moto_rest_api(context=context, rest_api_id=request.get("restApiId"))
        resource = moto_rest_api.resources.get(request.get("resourceId"))
        if not resource:
            raise NotFoundException("Invalid Resource identifier specified")

        method = resource.resource_methods.get(request.get("httpMethod"))
        if not method:
            raise NotFoundException("Invalid Method identifier specified")

        # TODO: if the IntegrationType is AWS, `credentials` is mandatory
        moto_request = copy.copy(request)
        moto_request.setdefault("passthroughBehavior", "WHEN_NO_MATCH")
        moto_request.setdefault("timeoutInMillis", 29000)
        if integration_type in (IntegrationType.HTTP, IntegrationType.HTTP_PROXY):
            moto_request.setdefault("connectionType", ConnectionType.INTERNET)

        response = call_moto_with_request(context, moto_request)
        remove_empty_attributes_from_integration(integration=response)

        # TODO: should fix fundamentally once we move away from moto
        if integration_type == "MOCK":
            response.pop("uri", None)

        # TODO: moto does not save the connection_id
        elif moto_request.get("connectionType") == "VPC_LINK":
            connection_id = moto_request.get("connectionId", "")
            # attach the connection id to the moto object
            method.method_integration.connection_id = connection_id
            response["connectionId"] = connection_id

        return response