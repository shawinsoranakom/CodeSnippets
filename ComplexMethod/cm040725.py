def put_function_event_invoke_config(
        self,
        context: RequestContext,
        function_name: FunctionName,
        qualifier: NumericLatestPublishedOrAliasQualifier = None,
        maximum_retry_attempts: MaximumRetryAttempts = None,
        maximum_event_age_in_seconds: MaximumEventAgeInSeconds = None,
        destination_config: DestinationConfig = None,
        **kwargs,
    ) -> FunctionEventInvokeConfig:
        """
        Destination ARNs can be:
        * SQS arn
        * SNS arn
        * Lambda arn
        * EventBridge arn

        Differences between put_ and update_:
            * put overwrites any existing config
            * update allows changes only single values while keeping the rest of existing ones
            * update fails on non-existing configs

        Differences between destination and DLQ
            * "However, a dead-letter queue is part of a function's version-specific configuration, so it is locked in when you publish a version."
            *  "On-failure destinations also support additional targets and include details about the function's response in the invocation record."

        """
        if (
            maximum_event_age_in_seconds is None
            and maximum_retry_attempts is None
            and destination_config is None
        ):
            raise InvalidParameterValueException(
                "You must specify at least one of error handling or destination setting.",
                Type="User",
            )
        account_id, region = api_utils.get_account_and_region(function_name, context)
        state = lambda_stores[account_id][region]
        function_name, qualifier = api_utils.get_name_and_qualifier(
            function_name, qualifier, context
        )
        fn = state.functions.get(function_name)
        if not fn or (qualifier and not (qualifier in fn.aliases or qualifier in fn.versions)):
            raise ResourceNotFoundException("The function doesn't exist.", Type="User")

        qualifier = qualifier or "$LATEST"

        # validate and normalize destination config
        if destination_config:
            self._validate_destination_config(state, function_name, destination_config)

        destination_config = DestinationConfig(
            OnSuccess=OnSuccess(
                Destination=(destination_config or {}).get("OnSuccess", {}).get("Destination")
            ),
            OnFailure=OnFailure(
                Destination=(destination_config or {}).get("OnFailure", {}).get("Destination")
            ),
        )

        config = EventInvokeConfig(
            function_name=function_name,
            qualifier=qualifier,
            maximum_event_age_in_seconds=maximum_event_age_in_seconds,
            maximum_retry_attempts=maximum_retry_attempts,
            last_modified=api_utils.generate_lambda_date(),
            destination_config=destination_config,
        )
        fn.event_invoke_configs[qualifier] = config

        return FunctionEventInvokeConfig(
            LastModified=datetime.datetime.strptime(
                config.last_modified, api_utils.LAMBDA_DATE_FORMAT
            ),
            FunctionArn=api_utils.qualified_lambda_arn(
                function_name, qualifier or "$LATEST", account_id, region
            ),
            DestinationConfig=destination_config,
            MaximumEventAgeInSeconds=maximum_event_age_in_seconds,
            MaximumRetryAttempts=maximum_retry_attempts,
        )