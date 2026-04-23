def validate_mock(test_state_input: TestStateInput) -> None:
        test_program, _ = TestStateAmazonStateLanguageParser.parse(
            test_state_input.get("definition"), test_state_input.get("stateName")
        )
        test_state = test_program.test_state
        mock_input = test_state_input.get("mock")

        TestStateStaticAnalyser.validate_test_state_allows_mocking(
            mock_input=mock_input, test_state=test_state
        )

        if mock_input is None:
            return

        if test_state_input.get("revealSecrets"):
            raise ValidationException(
                "TestState does not support RevealSecrets when a mock is specified."
            )

        if {"result", "errorOutput"} <= mock_input.keys():
            raise ValidationException(
                "A test mock should have only one of the following fields: [result, errorOutput]."
            )

        mock_result_raw = mock_input.get("result")
        if mock_result_raw is None:
            return
        try:
            mock_result = json.loads(mock_result_raw)
        except json.JSONDecodeError:
            raise ValidationException("Mocked result must be valid JSON")

        if isinstance(test_state, StateMap):
            TestStateStaticAnalyser.validate_mock_result_matches_map_definition(
                mock_result=mock_result, test_state=test_state
            )

        if isinstance(test_state, StateParallel):
            TestStateStaticAnalyser.validate_mock_result_matches_parallel_definition(
                mock_result=mock_result, test_state=test_state
            )

        if isinstance(test_state, StateTaskService):
            field_validation_mode = mock_input.get(
                "fieldValidationMode", MockResponseValidationMode.STRICT
            )
            TestStateStaticAnalyser.validate_mock_result_matches_api_shape(
                mock_result=mock_result,
                field_validation_mode=field_validation_mode,
                test_state=test_state,
            )