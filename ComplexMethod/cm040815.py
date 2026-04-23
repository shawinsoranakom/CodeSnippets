def create_state_machine(
        self, context: RequestContext, request: CreateStateMachineInput, **kwargs
    ) -> CreateStateMachineOutput:
        if not request.get("publish", False) and request.get("versionDescription"):
            raise ValidationException("Version description can only be set when publish is true")

        # Extract parameters and set defaults.
        state_machine_name = request["name"]
        state_machine_role_arn = request["roleArn"]
        state_machine_definition = request["definition"]
        state_machine_type = request.get("type") or StateMachineType.STANDARD
        state_machine_tracing_configuration = request.get("tracingConfiguration")
        state_machine_tags = request.get("tags")
        state_machine_logging_configuration = request.get(
            "loggingConfiguration", LoggingConfiguration()
        )
        self._sanitise_logging_configuration(
            logging_configuration=state_machine_logging_configuration
        )

        # CreateStateMachine is an idempotent API. Subsequent requests won't create a duplicate resource if it was
        # already created.
        idem_state_machine: StateMachineRevision | None = self._idempotent_revision(
            context=context,
            name=state_machine_name,
            definition=state_machine_definition,
            state_machine_type=state_machine_type,
            logging_configuration=state_machine_logging_configuration,
            tracing_configuration=state_machine_tracing_configuration,
        )
        if idem_state_machine is not None:
            return CreateStateMachineOutput(
                stateMachineArn=idem_state_machine.arn,
                creationDate=idem_state_machine.create_date,
            )

        # Assert this state machine name is unique.
        state_machine_with_name: StateMachineRevision | None = self._revision_by_name(
            context=context, name=state_machine_name
        )
        if state_machine_with_name is not None:
            raise StateMachineAlreadyExists(
                f"State Machine Already Exists: '{state_machine_with_name.arn}'"
            )

        # Compute the state machine's Arn.
        state_machine_arn = stepfunctions_state_machine_arn(
            name=state_machine_name,
            account_id=context.account_id,
            region_name=context.region,
        )
        state_machines = self.get_store(context).state_machines

        # Reduce the logging configuration to a usable cloud watch representation, and validate the destinations
        # if any were given.
        cloud_watch_logging_configuration = (
            CloudWatchLoggingConfiguration.from_logging_configuration(
                state_machine_arn=state_machine_arn,
                logging_configuration=state_machine_logging_configuration,
            )
        )
        if cloud_watch_logging_configuration is not None:
            cloud_watch_logging_configuration.validate()

        # Run static analysers on the definition given.
        if state_machine_type == StateMachineType.EXPRESS:
            StepFunctionsProvider._validate_definition(
                definition=state_machine_definition,
                static_analysers=[ExpressStaticAnalyser()],
            )
        else:
            StepFunctionsProvider._validate_definition(
                definition=state_machine_definition, static_analysers=[StaticAnalyser()]
            )

        # Create the state machine and add it to the store.
        state_machine = StateMachineRevision(
            name=state_machine_name,
            arn=state_machine_arn,
            role_arn=state_machine_role_arn,
            definition=state_machine_definition,
            sm_type=state_machine_type,
            logging_config=state_machine_logging_configuration,
            cloud_watch_logging_configuration=cloud_watch_logging_configuration,
            tracing_config=state_machine_tracing_configuration,
            tags=state_machine_tags,
        )
        state_machines[state_machine_arn] = state_machine

        create_output = CreateStateMachineOutput(
            stateMachineArn=state_machine.arn, creationDate=state_machine.create_date
        )

        # Create the first version if the 'publish' flag is used.
        if request.get("publish", False):
            version_description = request.get("versionDescription")
            state_machine_version = state_machine.create_version(description=version_description)
            if state_machine_version is not None:
                state_machine_version_arn = state_machine_version.arn
                state_machines[state_machine_version_arn] = state_machine_version
                create_output["stateMachineVersionArn"] = state_machine_version_arn

        # Run static analyser on definition and collect usage metrics
        UsageMetricsStaticAnalyser.process(state_machine_definition)

        return create_output