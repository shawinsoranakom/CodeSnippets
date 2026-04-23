def start_execution(
        self,
        context: RequestContext,
        state_machine_arn: Arn,
        name: Name = None,
        input: SensitiveData = None,
        trace_header: TraceHeader = None,
        **kwargs,
    ) -> StartExecutionOutput:
        self._validate_state_machine_arn(state_machine_arn)

        base_arn = self._get_state_machine_arn(state_machine_arn)
        store = self.get_store(context=context)

        alias: Alias | None = store.aliases.get(base_arn)
        alias_sample_state_machine_version_arn = alias.sample() if alias is not None else None
        unsafe_state_machine: StateMachineInstance | None = store.state_machines.get(
            alias_sample_state_machine_version_arn or base_arn
        )
        if not unsafe_state_machine:
            self._raise_state_machine_does_not_exist(base_arn)

        # Update event change parameters about the state machine and should not affect those about this execution.
        state_machine_clone = copy.deepcopy(unsafe_state_machine)

        if input is None:
            input_data = {}
        else:
            try:
                input_data = json.loads(input)
            except Exception as ex:
                raise InvalidExecutionInput(str(ex))  # TODO: report parsing error like AWS.

        normalised_state_machine_arn = (
            state_machine_clone.source_arn
            if isinstance(state_machine_clone, StateMachineVersion)
            else state_machine_clone.arn
        )
        exec_name = name or long_uid()  # TODO: validate name format
        if state_machine_clone.sm_type == StateMachineType.STANDARD:
            exec_arn = stepfunctions_standard_execution_arn(normalised_state_machine_arn, exec_name)
        else:
            # Exhaustive check on STANDARD and EXPRESS type, validated on creation.
            exec_arn = stepfunctions_express_execution_arn(normalised_state_machine_arn, exec_name)

        if execution := store.executions.get(exec_arn):
            # Return already running execution if name and input match
            existing_execution = self._idempotent_start_execution(
                execution=execution,
                state_machine=state_machine_clone,
                name=name,
                input_data=input_data,
            )

            if existing_execution:
                return existing_execution.to_start_output()

        # Create the execution logging session, if logging is configured.
        cloud_watch_logging_session = None
        if state_machine_clone.cloud_watch_logging_configuration is not None:
            cloud_watch_logging_session = CloudWatchLoggingSession(
                execution_arn=exec_arn,
                configuration=state_machine_clone.cloud_watch_logging_configuration,
            )

        local_mock_test_case = self._get_local_mock_test_case(
            state_machine_arn, state_machine_clone.name
        )

        execution = Execution(
            name=exec_name,
            sm_type=state_machine_clone.sm_type,
            role_arn=state_machine_clone.role_arn,
            exec_arn=exec_arn,
            account_id=context.account_id,
            region_name=context.region,
            state_machine=state_machine_clone,
            state_machine_alias_arn=alias.state_machine_alias_arn if alias is not None else None,
            start_date=datetime.datetime.now(tz=datetime.UTC),
            cloud_watch_logging_session=cloud_watch_logging_session,
            input_data=input_data,
            trace_header=trace_header,
            activity_store=self.get_store(context).activities,
            local_mock_test_case=local_mock_test_case,
        )

        store.executions[exec_arn] = execution

        execution.start()
        return execution.to_start_output()