def to_test_state_output(self, inspection_level: InspectionLevel) -> TestStateOutput:
        exit_program_state: ProgramState = self.exec_worker.env.program_state()
        if isinstance(exit_program_state, ProgramEnded):
            output_str = to_json_str(self.output)
            test_state_output = TestStateOutput(
                status=TestExecutionStatus.SUCCEEDED, output=output_str
            )
        elif isinstance(exit_program_state, ProgramError):
            test_state_output = TestStateOutput(
                status=TestExecutionStatus.FAILED,
                error=exit_program_state.error["error"],
                cause=exit_program_state.error["cause"],
            )
        elif isinstance(exit_program_state, ProgramChoiceSelected):
            output_str = to_json_str(self.output)
            test_state_output = TestStateOutput(
                status=TestExecutionStatus.SUCCEEDED, nextState=self.next_state, output=output_str
            )
        elif isinstance(exit_program_state, ProgramCaughtError):
            output_str = to_json_str(self.output)
            test_state_output = TestStateOutput(
                status=TestExecutionStatus.CAUGHT_ERROR,
                nextState=self.next_state,
                output=output_str,
                error=exit_program_state.error,
                cause=exit_program_state.cause,
            )
        elif isinstance(exit_program_state, ProgramRetriable):
            test_state_output = TestStateOutput(
                status=TestExecutionStatus.RETRIABLE,
                error=exit_program_state.error,
                cause=exit_program_state.cause,
            )
        else:
            # TODO: handle other statuses
            LOG.warning(
                "Unsupported StateMachine exit type for TestState '%s'",
                type(exit_program_state),
            )
            output_str = to_json_str(self.output)
            test_state_output = TestStateOutput(
                status=TestExecutionStatus.FAILED, output=output_str
            )

        match inspection_level:
            case InspectionLevel.TRACE:
                test_state_output["inspectionData"] = self.exec_worker.env.inspection_data
            case InspectionLevel.DEBUG:
                test_state_output["inspectionData"] = self.exec_worker.env.inspection_data

        return test_state_output