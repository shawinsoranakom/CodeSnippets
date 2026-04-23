def test_request_id_async_invoke_with_retry(
        self, aws_client, create_lambda_function, monkeypatch, snapshot
    ):
        snapshot.add_transformer(
            snapshot.transform.key_value("eventId", "<event-id>", reference_replacement=False)
        )
        test_delay_base = 60
        if not is_aws_cloud():
            test_delay_base = 5
            monkeypatch.setattr(config, "LAMBDA_RETRY_BASE_DELAY_SECONDS", test_delay_base)

        func_name = f"test_lambda_{short_uid()}"
        log_group_name = f"/aws/lambda/{func_name}"
        create_lambda_function(
            func_name=func_name,
            handler_file=TEST_LAMBDA_CONTEXT_REQID,
            runtime=Runtime.python3_12,
            client=aws_client.lambda_,
        )

        aws_client.lambda_.put_function_event_invoke_config(
            FunctionName=func_name, MaximumRetryAttempts=1
        )
        aws_client.lambda_.get_waiter("function_updated_v2").wait(FunctionName=func_name)

        result = aws_client.lambda_.invoke(
            FunctionName=func_name, InvocationType="Event", Payload=json.dumps({"fail": 1})
        )
        snapshot.match("invoke_result", result)

        request_id = result["ResponseMetadata"]["RequestId"]
        snapshot.add_transformer(snapshot.transform.regex(request_id, "<request-id>"))

        time.sleep(test_delay_base * 2)

        log_events = aws_client.logs.filter_log_events(logGroupName=log_group_name)
        report_messages = [e for e in log_events["events"] if "REPORT" in e["message"]]
        assert len(report_messages) == 2
        assert all(request_id in rm["message"] for rm in report_messages)
        end_messages = [
            e["message"].rstrip() for e in log_events["events"] if "END" in e["message"]
        ]
        snapshot.match("end_messages", end_messages)