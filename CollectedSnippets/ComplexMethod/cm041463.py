def test_lambda_sqs_integration_retry_path(
        self,
        aws_client,
        monkeypatch,
        mock_config_file,
    ):
        execution_arn = create_and_run_mock(
            target_aws_client=aws_client,
            monkeypatch=monkeypatch,
            mock_config_file=mock_config_file,
            mock_config=MockedServiceIntegrationsLoader.load(
                MockedServiceIntegrationsLoader.MOCK_CONFIG_FILE_LAMBDA_SQS_INTEGRATION
            ),
            state_machine_name="LambdaSQSIntegration",
            definition_template=MockedTemplates.load_sfn_template(
                MockedTemplates.LAMBDA_SQS_INTEGRATION
            ),
            execution_input="{}",
            test_name="RetryPath",
        )

        execution_history = aws_client.stepfunctions.get_execution_history(
            executionArn=execution_arn, includeExecutionData=True
        )
        events = execution_history["events"]

        event_4 = events[4]
        assert event_4["taskFailedEventDetails"] == {
            "error": "Lambda.ResourceNotReadyException",
            "cause": "Lambda resource is not ready.",
        }
        assert event_4["type"] == "TaskFailed"

        event_7 = events[7]
        assert event_7["taskFailedEventDetails"] == {
            "error": "Lambda.TimeoutException",
            "cause": "Lambda timed out.",
        }
        assert event_7["type"] == "TaskFailed"

        event_10 = events[10]
        assert event_10["taskFailedEventDetails"] == {
            "error": "Lambda.TimeoutException",
            "cause": "Lambda timed out.",
        }
        assert event_10["type"] == "TaskFailed"

        event_13 = events[13]
        assert json.loads(event_13["taskSucceededEventDetails"]["output"]) == {
            "StatusCode": 200,
            "Payload": {"StatusCode": 200, "body": "Hello from Lambda!"},
        }

        event_last = events[-1]
        assert event_last["type"] == "ExecutionSucceeded"