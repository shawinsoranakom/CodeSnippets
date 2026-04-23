def validate_event_source_mapping(self, context, request):
        # TODO: test whether stream ARNs are valid sources for Pipes or ESM or whether only DynamoDB table ARNs work
        # TODO: Validate MaxRecordAgeInSeconds (i.e cannot subceed 60s but can be -1) and MaxRetryAttempts parameters.
        # See https://docs.aws.amazon.com/AWSCloudFormation/latest/UserGuide/aws-resource-lambda-eventsourcemapping.html#cfn-lambda-eventsourcemapping-maximumrecordageinseconds
        is_create_esm_request = context.operation.name == self.create_event_source_mapping.operation

        if destination_config := request.get("DestinationConfig"):
            if "OnSuccess" in destination_config:
                raise InvalidParameterValueException(
                    "Unsupported DestinationConfig parameter for given event source mapping type.",
                    Type="User",
                )

        service = None
        if "SelfManagedEventSource" in request:
            service = "kafka"
            if "SourceAccessConfigurations" not in request:
                raise InvalidParameterValueException(
                    "Required 'sourceAccessConfigurations' parameter is missing.", Type="User"
                )
        if service is None and "EventSourceArn" not in request:
            raise InvalidParameterValueException("Unrecognized event source.", Type="User")
        if service is None:
            service = extract_service_from_arn(request["EventSourceArn"])

        batch_size = api_utils.validate_and_set_batch_size(service, request.get("BatchSize"))
        if service in ["dynamodb", "kinesis"]:
            starting_position = request.get("StartingPosition")
            if not starting_position:
                raise InvalidParameterValueException(
                    "1 validation error detected: Value null at 'startingPosition' failed to satisfy constraint: Member must not be null.",
                    Type="User",
                )

            if starting_position not in KinesisStreamStartPosition.__members__:
                raise ValidationException(
                    f"1 validation error detected: Value '{starting_position}' at 'startingPosition' failed to satisfy constraint: Member must satisfy enum value set: [LATEST, AT_TIMESTAMP, TRIM_HORIZON]"
                )
            # AT_TIMESTAMP is not allowed for DynamoDB Streams
            elif (
                service == "dynamodb"
                and starting_position not in DynamoDBStreamStartPosition.__members__
            ):
                raise InvalidParameterValueException(
                    f"Unsupported starting position for arn type: {request['EventSourceArn']}",
                    Type="User",
                )

        if service in ["sqs", "sqs-fifo"]:
            if batch_size > 10 and request.get("MaximumBatchingWindowInSeconds", 0) == 0:
                raise InvalidParameterValueException(
                    "Maximum batch window in seconds must be greater than 0 if maximum batch size is greater than 10",
                    Type="User",
                )

        if (filter_criteria := request.get("FilterCriteria")) is not None:
            for filter_ in filter_criteria.get("Filters", []):
                pattern_str = filter_.get("Pattern")
                if not pattern_str or not isinstance(pattern_str, str):
                    raise InvalidParameterValueException(
                        "Invalid filter pattern definition.", Type="User"
                    )

                if not validate_event_pattern(pattern_str):
                    raise InvalidParameterValueException(
                        "Invalid filter pattern definition.", Type="User"
                    )

        # Can either have a FunctionName (i.e CreateEventSourceMapping request) or
        # an internal EventSourceMappingConfiguration representation
        request_function_name = request.get("FunctionName") or request.get("FunctionArn")
        # can be either a partial arn or a full arn for the version/alias
        function_name, qualifier, account, region = function_locators_from_arn(
            request_function_name
        )
        # TODO: validate `context.region` vs. `region(request["FunctionName"])` vs. `region(request["EventSourceArn"])`
        account = account or context.account_id
        region = region or context.region
        state = lambda_stores[account][region]
        fn = state.functions.get(function_name)
        if not fn:
            raise InvalidParameterValueException("Function does not exist", Type="User")

        if qualifier:
            # make sure the function version/alias exists
            if api_utils.qualifier_is_alias(qualifier):
                fn_alias = fn.aliases.get(qualifier)
                if not fn_alias:
                    raise Exception("unknown alias")  # TODO: cover via test
            elif api_utils.qualifier_is_version(qualifier):
                fn_version = fn.versions.get(qualifier)
                if not fn_version:
                    raise Exception("unknown version")  # TODO: cover via test
            elif qualifier == "$LATEST":
                pass
            elif qualifier == "$LATEST.PUBLISHED":
                if fn.versions.get(qualifier):
                    pass
            else:
                raise Exception("invalid functionname")  # TODO: cover via test
            fn_arn = api_utils.qualified_lambda_arn(function_name, qualifier, account, region)

        else:
            fn_arn = api_utils.unqualified_lambda_arn(function_name, account, region)

        function_version = get_function_version_from_arn(fn_arn)
        function_role = function_version.config.role

        if source_arn := request.get("EventSourceArn"):
            self.check_service_resource_exists(service, source_arn, fn_arn, function_role)
        # Check we are validating a CreateEventSourceMapping request
        if is_create_esm_request:

            def _get_mapping_sources(mapping: dict[str, Any]) -> list[str]:
                if event_source_arn := mapping.get("EventSourceArn"):
                    return [event_source_arn]
                return (
                    mapping.get("SelfManagedEventSource", {})
                    .get("Endpoints", {})
                    .get("KAFKA_BOOTSTRAP_SERVERS", [])
                )

            # check for event source duplicates
            # TODO: currently validated for sqs, kinesis, and dynamodb
            service_id = load_service(service).service_id
            for uuid, mapping in state.event_source_mappings.items():
                mapping_sources = _get_mapping_sources(mapping)
                request_sources = _get_mapping_sources(request)
                if mapping["FunctionArn"] == fn_arn and (
                    set(mapping_sources).intersection(request_sources)
                ):
                    if service == "sqs":
                        # *shakes fist at SQS*
                        raise ResourceConflictException(
                            f'An event source mapping with {service_id} arn (" {mapping["EventSourceArn"]} ") '
                            f'and function (" {function_name} ") already exists. Please update or delete the '
                            f"existing mapping with UUID {uuid}",
                            Type="User",
                        )
                    elif service == "kafka":
                        if set(mapping["Topics"]).intersection(request["Topics"]):
                            raise ResourceConflictException(
                                f'An event source mapping with event source ("{",".join(request_sources)}"), '
                                f'function ("{fn_arn}"), '
                                f'topics ("{",".join(request["Topics"])}") already exists. Please update or delete the '
                                f"existing mapping with UUID {uuid}",
                                Type="User",
                            )
                    else:
                        raise ResourceConflictException(
                            f'The event source arn (" {mapping["EventSourceArn"]} ") and function '
                            f'(" {function_name} ") provided mapping already exists. Please update or delete the '
                            f"existing mapping with UUID {uuid}",
                            Type="User",
                        )
        return fn_arn, function_name, state, function_version, function_role