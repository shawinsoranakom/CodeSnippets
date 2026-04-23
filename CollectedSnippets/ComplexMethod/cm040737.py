def invoke(
        self,
        function_name: str,
        qualifier: str | None,
        region: str,
        account_id: str,
        invocation_type: InvocationType | None,
        client_context: str | None,
        request_id: str,
        payload: bytes | None,
        trace_context: dict | None = None,
        user_agent: str | None = None,
    ) -> InvocationResult | None:
        """
        Invokes a specific version of a lambda

        :param request_id: context request ID
        :param function_name: Function name
        :param qualifier: Function version qualifier
        :param region: Region of the function
        :param account_id: Account id of the function
        :param invocation_type: Invocation Type
        :param client_context: Client Context, if applicable
        :param trace_context: tracing information such as X-Ray header
        :param payload: Invocation payload
        :return: The invocation result
        """
        # NOTE: consider making the trace_context mandatory once we update all usages (should be easier after v4.0)
        trace_context = trace_context or {}
        # Invoked arn (for lambda context) does not have qualifier if not supplied
        invoked_arn = lambda_arn(
            function_name=function_name,
            qualifier=qualifier,
            account=account_id,
            region=region,
        )
        state = lambda_stores[account_id][region]
        function = state.functions.get(function_name)

        if function is None:
            if not qualifier:
                invoked_arn += ":$LATEST"
            raise ResourceNotFoundException(f"Function not found: {invoked_arn}", Type="User")

        # A provided qualifier always takes precedence, but the default depends on whether $LATEST.PUBLISHED exists
        version_latest_published = function.versions.get("$LATEST.PUBLISHED")
        if version_latest_published:
            qualifier = qualifier or "$LATEST.PUBLISHED"
            invoked_arn = lambda_arn(
                function_name=function_name,
                qualifier=qualifier,
                account=account_id,
                region=region,
            )
        else:
            qualifier = qualifier or "$LATEST"

        if qualifier_is_alias(qualifier):
            alias = function.aliases.get(qualifier)
            if not alias:
                raise ResourceNotFoundException(f"Function not found: {invoked_arn}", Type="User")
            version_qualifier = alias.function_version
            if alias.routing_configuration:
                version, probability = next(
                    iter(alias.routing_configuration.version_weights.items())
                )
                if random.random() < probability:
                    version_qualifier = version
        else:
            version_qualifier = qualifier

        # Need the qualified arn to exactly get the target lambda
        qualified_arn = qualified_lambda_arn(function_name, version_qualifier, account_id, region)
        version = function.versions.get(version_qualifier)
        if version is None:
            raise ResourceNotFoundException(f"Function not found: {invoked_arn}", Type="User")
        runtime = version.config.runtime or "n/a"
        package_type = version.config.package_type
        # Not considering provisioned concurrency for such early errors
        initialization_type = (
            FunctionInitializationType.lambda_managed_instances
            if version.config.capacity_provider_config
            else FunctionInitializationType.on_demand
        )
        if version.config.capacity_provider_config and qualifier == "$LATEST":
            if function.versions.get("$LATEST.PUBLISHED"):
                raise InvalidParameterValueException(
                    "Functions configured with capacity provider configuration can't be invoked with $LATEST qualifier. To invoke this function, specify a published version qualifier or $LATEST.PUBLISHED.",
                    Type="User",
                )
            else:
                raise NoPublishedVersionException(
                    "The function can't be invoked because no published version exists. For functions with capacity provider configuration, either publish a version to $LATEST.PUBLISHED, or specify a published version qualifier.",
                    Type="User",
                )
        try:
            version_manager = self.get_lambda_version_manager(qualified_arn)
            event_manager = self.get_lambda_event_manager(qualified_arn)
        except ValueError as e:
            state = version and version.config.state.state
            if state == State.Failed:
                status = FunctionStatus.failed_state_error
                HINT_LOG.error(
                    f"Failed to create the runtime executor for the function {function_name}. "
                    "Please ensure that Docker is available in the LocalStack container by adding the volume mount "
                    '"/var/run/docker.sock:/var/run/docker.sock" to your LocalStack startup. '
                    "Check out https://docs.localstack.cloud/user-guide/aws/lambda/#docker-not-available"
                )
            elif state == State.Pending:
                status = FunctionStatus.pending_state_error
                HINT_LOG.warning(
                    "Lambda functions are created and updated asynchronously in the new lambda provider like in AWS. "
                    f"Before invoking {function_name}, please wait until the function transitioned from the state "
                    "Pending to Active using: "
                    f'"awslocal lambda wait function-active-v2 --function-name {function_name}" '
                    "Check out https://docs.localstack.cloud/user-guide/aws/lambda/#function-in-pending-state"
                )
            else:
                status = FunctionStatus.unhandled_state_error
                LOG.error("Unexpected state %s for Lambda function %s", state, function_name)
            function_counter.labels(
                operation=FunctionOperation.invoke,
                runtime=runtime,
                status=status,
                invocation_type=invocation_type,
                package_type=package_type,
                initialization_type=initialization_type,
            ).increment()
            raise ResourceConflictException(
                f"The operation cannot be performed at this time. The function is currently in the following state: {state}"
            ) from e
        # empty payloads have to work as well
        if payload is None:
            payload = b"{}"
        else:
            # detect invalid payloads early before creating an execution environment
            try:
                to_str(payload)
            except Exception as e:
                function_counter.labels(
                    operation=FunctionOperation.invoke,
                    runtime=runtime,
                    status=FunctionStatus.invalid_payload_error,
                    invocation_type=invocation_type,
                    package_type=package_type,
                    initialization_type=initialization_type,
                ).increment()
                # MAYBE: improve parity of detailed exception message (quite cumbersome)
                raise InvalidRequestContentException(
                    f"Could not parse request body into json: Could not parse payload into json: {e}",
                    Type="User",
                )
        if invocation_type is None:
            invocation_type = InvocationType.RequestResponse
        if invocation_type == InvocationType.DryRun:
            return None
        # TODO payload verification  An error occurred (InvalidRequestContentException) when calling the Invoke operation: Could not parse request body into json: Could not parse payload into json: Unexpected character (''' (code 39)): expected a valid value (JSON String, Number, Array, Object or token 'null', 'true' or 'false')
        #  at [Source: (byte[])"'test'"; line: 1, column: 2]
        #
        if invocation_type == InvocationType.Event:
            return event_manager.enqueue_event(
                invocation=Invocation(
                    payload=payload,
                    invoked_arn=invoked_arn,
                    client_context=client_context,
                    invocation_type=invocation_type,
                    invoke_time=datetime.now(),
                    request_id=request_id,
                    trace_context=trace_context,
                    user_agent=user_agent,
                )
            )

        invocation_result = version_manager.invoke(
            invocation=Invocation(
                payload=payload,
                invoked_arn=invoked_arn,
                client_context=client_context,
                invocation_type=invocation_type,
                invoke_time=datetime.now(),
                request_id=request_id,
                trace_context=trace_context,
                user_agent=user_agent,
            )
        )
        status = (
            FunctionStatus.invocation_error
            if invocation_result.is_error
            else FunctionStatus.success
        )
        # TODO: handle initialization_type provisioned-concurrency, requires enriching invocation_result
        function_counter.labels(
            operation=FunctionOperation.invoke,
            runtime=runtime,
            status=status,
            invocation_type=invocation_type,
            package_type=package_type,
            initialization_type=initialization_type,
        ).increment()
        return invocation_result