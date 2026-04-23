def update_function_url_config(
        self,
        context: RequestContext,
        function_name: FunctionName,
        qualifier: FunctionUrlQualifier = None,
        auth_type: FunctionUrlAuthType = None,
        cors: Cors = None,
        invoke_mode: InvokeMode = None,
        **kwargs,
    ) -> UpdateFunctionUrlConfigResponse:
        account_id, region = api_utils.get_account_and_region(function_name, context)
        state = lambda_stores[account_id][region]

        function_name, qualifier = api_utils.get_name_and_qualifier(
            function_name, qualifier, context
        )
        self._validate_qualifier(qualifier)
        self._validate_invoke_mode(invoke_mode)

        fn = state.functions.get(function_name)
        if not fn:
            raise ResourceNotFoundException("Function does not exist", Type="User")

        normalized_qualifier = qualifier or "$LATEST"

        if (
            api_utils.qualifier_is_alias(normalized_qualifier)
            and normalized_qualifier not in fn.aliases
        ):
            raise ResourceNotFoundException("Function does not exist", Type="User")

        url_config = fn.function_url_configs.get(normalized_qualifier)
        if not url_config:
            raise ResourceNotFoundException(
                "The resource you requested does not exist.", Type="User"
            )

        changes = {
            "last_modified_time": api_utils.generate_lambda_date(),
            **({"cors": cors} if cors is not None else {}),
            **({"auth_type": auth_type} if auth_type is not None else {}),
        }

        if invoke_mode:
            changes["invoke_mode"] = invoke_mode

        new_url_config = dataclasses.replace(url_config, **changes)
        fn.function_url_configs[normalized_qualifier] = new_url_config

        return UpdateFunctionUrlConfigResponse(
            FunctionUrl=new_url_config.url,
            FunctionArn=new_url_config.function_arn,
            AuthType=new_url_config.auth_type,
            Cors=new_url_config.cors,
            CreationTime=new_url_config.creation_time,
            LastModifiedTime=new_url_config.last_modified_time,
            InvokeMode=new_url_config.invoke_mode,
        )