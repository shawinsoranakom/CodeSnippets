def test_state(
        self, context: RequestContext, request: TestStateInput, **kwargs
    ) -> TestStateOutput:
        state_name = request.get("stateName")
        definition = request["definition"]

        StepFunctionsProvider._validate_definition(
            definition=definition,
            static_analysers=[TestStateStaticAnalyser(state_name)],
        )

        # if StateName is present, we need to ensure the state being referenced exists in full definition.
        if state_name and not TestStateStaticAnalyser.is_state_in_definition(
            definition=definition, state_name=state_name
        ):
            raise ValidationException("State not found in definition")

        mock_input = request.get("mock")
        state_configuration = request.get("stateConfiguration")

        TestStateStaticAnalyser.validate_state_configuration(state_configuration, mock_input)
        TestStateStaticAnalyser.validate_mock(test_state_input=request)

        if state_context := request.get("context"):
            # TODO: Add validation ensuring only present if 'mock' is specified
            # An error occurred (ValidationException) when calling the TestState operation: State type 'Pass' is not supported when a mock is specified
            pass

        try:
            state_mock = TestStateMock(
                mock_input=mock_input,
                state_configuration=state_configuration,
                context=state_context,
            )
        except ValueError as e:
            LOG.error(e)
            raise ValidationException(f"Invalid Context object provided: {e}")

        name: Name | None = f"TestState-{short_uid()}"
        arn = stepfunctions_state_machine_arn(
            name=name, account_id=context.account_id, region_name=context.region
        )
        role_arn = request.get("roleArn")
        if role_arn is None:
            TestStateStaticAnalyser.validate_role_arn_required(
                mock_input=mock_input, definition=definition, state_name=state_name
            )
            # HACK: Added dummy role ARN because it is a required field in Execution.
            # To allow optional roleArn for the test state but preserve the mandatory one for regular executions
            # we likely need to remove inheritance TestStateExecution(Execution) in favor of composition.
            # TestState execution starts to have too many simplifications compared to a regular execution
            # which renders the inheritance mechanism harmful.
            # TODO make role_arn optional in TestStateExecution
            role_arn = arns.iam_role_arn(
                role_name=f"RoleFor-{name}",
                account_id=context.account_id,
                region_name=context.region,
            )

        state_machine = TestStateMachine(
            name=name,
            arn=arn,
            role_arn=role_arn,
            definition=request["definition"],
        )

        # HACK(gregfurman): The ARN that gets generated has a duplicate 'name' field in the
        # resource ARN. Just replace this duplication and extract the execution ID.
        exec_arn = stepfunctions_express_execution_arn(state_machine.arn, name)
        exec_arn = exec_arn.replace(f":{name}:{name}:", f":{name}:", 1)
        _, exec_name = exec_arn.rsplit(":", 1)

        if input_json := request.get("input", {}):
            input_json = json.loads(input_json)

        if variables_json := request.get("variables"):
            variables_json = json.loads(variables_json)

        execution = TestStateExecution(
            name=exec_name,
            role_arn=role_arn,
            exec_arn=exec_arn,
            account_id=context.account_id,
            region_name=context.region,
            state_machine=state_machine,
            start_date=datetime.datetime.now(tz=datetime.UTC),
            input_data=input_json,
            state_name=state_name,
            activity_store=self.get_store(context).activities,
            mock=state_mock,
            variables=variables_json,
        )
        execution.start()

        test_state_output = execution.to_test_state_output(
            inspection_level=request.get("inspectionLevel", InspectionLevel.INFO)
        )

        return test_state_output