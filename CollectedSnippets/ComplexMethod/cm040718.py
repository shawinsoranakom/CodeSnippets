def create_function_url_config(
        self,
        context: RequestContext,
        function_name: FunctionName,
        auth_type: FunctionUrlAuthType,
        qualifier: FunctionUrlQualifier = None,
        cors: Cors = None,
        invoke_mode: InvokeMode = None,
        **kwargs,
    ) -> CreateFunctionUrlConfigResponse:
        account_id, region = api_utils.get_account_and_region(function_name, context)
        function_name, qualifier = api_utils.get_name_and_qualifier(
            function_name, qualifier, context
        )
        state = lambda_stores[account_id][region]
        self._validate_qualifier(qualifier)
        self._validate_invoke_mode(invoke_mode)

        fn = state.functions.get(function_name)
        if fn is None:
            raise ResourceNotFoundException("Function does not exist", Type="User")

        url_config = fn.function_url_configs.get(qualifier or "$LATEST")
        if url_config:
            raise ResourceConflictException(
                f"Failed to create function url config for [functionArn = {url_config.function_arn}]. Error message:  FunctionUrlConfig exists for this Lambda function",
                Type="User",
            )

        if qualifier and qualifier != "$LATEST" and qualifier not in fn.aliases:
            raise ResourceNotFoundException("Function does not exist", Type="User")

        normalized_qualifier = qualifier or "$LATEST"

        function_arn = (
            api_utils.qualified_lambda_arn(function_name, qualifier, account_id, region)
            if qualifier
            else api_utils.unqualified_lambda_arn(function_name, account_id, region)
        )

        custom_id: str | None = None

        tags = self._get_tags(api_utils.unqualified_lambda_arn(function_name, account_id, region))
        if TAG_KEY_CUSTOM_URL in tags:
            # Note: I really wanted to add verification here that the
            # url_id is unique, so we could surface that to the user ASAP.
            # However, it seems like that information isn't available yet,
            # since (as far as I can tell) we call
            # self.router.register_routes() once, in a single shot, for all
            # of the routes -- and we need to verify that it's unique not
            # just for this particular lambda function, but for the entire
            # lambda provider. Therefore... that idea proved non-trivial!
            custom_id_tag_value = (
                f"{tags[TAG_KEY_CUSTOM_URL]}-{qualifier}" if qualifier else tags[TAG_KEY_CUSTOM_URL]
            )
            if TAG_KEY_CUSTOM_URL_VALIDATOR.match(custom_id_tag_value):
                custom_id = custom_id_tag_value

            else:
                # Note: we're logging here instead of raising to prioritize
                # strict parity with AWS over the localstack-only custom_id
                LOG.warning(
                    "Invalid custom ID tag value for lambda URL (%s=%s). "
                    "Replaced with default (random id)",
                    TAG_KEY_CUSTOM_URL,
                    custom_id_tag_value,
                )

        # The url_id is the subdomain used for the URL we're creating. This
        # is either created randomly (as in AWS), or can be passed as a tag
        # to the lambda itself (localstack-only).
        url_id: str
        if custom_id is None:
            url_id = api_utils.generate_random_url_id()
        else:
            url_id = custom_id

        host_definition = localstack_host(custom_port=config.GATEWAY_LISTEN[0].port)
        fn.function_url_configs[normalized_qualifier] = FunctionUrlConfig(
            function_arn=function_arn,
            function_name=function_name,
            cors=cors,
            url_id=url_id,
            url=f"http://{url_id}.lambda-url.{context.region}.{host_definition.host_and_port()}/",  # TODO: https support
            auth_type=auth_type,
            creation_time=api_utils.generate_lambda_date(),
            last_modified_time=api_utils.generate_lambda_date(),
            invoke_mode=invoke_mode,
        )

        # persist and start URL
        # TODO: implement URL invoke
        api_url_config = api_utils.map_function_url_config(
            fn.function_url_configs[normalized_qualifier]
        )

        return CreateFunctionUrlConfigResponse(
            FunctionUrl=api_url_config["FunctionUrl"],
            FunctionArn=api_url_config["FunctionArn"],
            AuthType=api_url_config["AuthType"],
            Cors=api_url_config["Cors"],
            CreationTime=api_url_config["CreationTime"],
            InvokeMode=api_url_config["InvokeMode"],
        )