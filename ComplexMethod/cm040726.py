def update_function_event_invoke_config(
        self,
        context: RequestContext,
        function_name: FunctionName,
        qualifier: NumericLatestPublishedOrAliasQualifier = None,
        maximum_retry_attempts: MaximumRetryAttempts = None,
        maximum_event_age_in_seconds: MaximumEventAgeInSeconds = None,
        destination_config: DestinationConfig = None,
        **kwargs,
    ) -> FunctionEventInvokeConfig:
        # like put but only update single fields via replace
        account_id, region = api_utils.get_account_and_region(function_name, context)
        state = lambda_stores[account_id][region]
        function_name, qualifier = api_utils.get_name_and_qualifier(
            function_name, qualifier, context
        )

        if (
            maximum_event_age_in_seconds is None
            and maximum_retry_attempts is None
            and destination_config is None
        ):
            raise InvalidParameterValueException(
                "You must specify at least one of error handling or destination setting.",
                Type="User",
            )

        fn = state.functions.get(function_name)
        if not fn or (qualifier and not (qualifier in fn.aliases or qualifier in fn.versions)):
            raise ResourceNotFoundException("The function doesn't exist.", Type="User")

        qualifier = qualifier or "$LATEST"

        config = fn.event_invoke_configs.get(qualifier)
        if not config:
            fn_arn = api_utils.qualified_lambda_arn(function_name, qualifier, account_id, region)
            raise ResourceNotFoundException(
                f"The function {fn_arn} doesn't have an EventInvokeConfig", Type="User"
            )

        if destination_config:
            self._validate_destination_config(state, function_name, destination_config)

        optional_kwargs = {
            k: v
            for k, v in {
                "destination_config": destination_config,
                "maximum_retry_attempts": maximum_retry_attempts,
                "maximum_event_age_in_seconds": maximum_event_age_in_seconds,
            }.items()
            if v is not None
        }

        new_config = dataclasses.replace(
            config, last_modified=api_utils.generate_lambda_date(), **optional_kwargs
        )
        fn.event_invoke_configs[qualifier] = new_config

        return FunctionEventInvokeConfig(
            LastModified=datetime.datetime.strptime(
                new_config.last_modified, api_utils.LAMBDA_DATE_FORMAT
            ),
            FunctionArn=api_utils.qualified_lambda_arn(
                function_name, qualifier or "$LATEST", account_id, region
            ),
            DestinationConfig=new_config.destination_config,
            MaximumEventAgeInSeconds=new_config.maximum_event_age_in_seconds,
            MaximumRetryAttempts=new_config.maximum_retry_attempts,
        )