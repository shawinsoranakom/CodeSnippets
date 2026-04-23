def test_retries(
        self,
        snapshot,
        create_lambda_function,
        sqs_create_queue,
        sqs_get_queue_arn,
        lambda_su_role,
        monkeypatch,
        aws_client,
    ):
        """
        behavior test, we don't really care about any API surface here right now

        this is quite long since lambda waits 1 minute between the invoke and first retry and 2 minutes between the first retry and the second retry!
        TODO: test if invocation/request ID changes between retries
        """
        snapshot.add_transformer(snapshot.transform.lambda_api())
        snapshot.add_transformer(snapshot.transform.sqs_api())
        snapshot.add_transformer(
            snapshot.transform.key_value(
                "MD5OfBody", value_replacement="<md5-body>", reference_replacement=False
            )
        )
        snapshot.add_transformer(snapshot.transform.key_value("AWSTraceHeader"))

        test_delay_base = 60
        if not is_aws_cloud():
            test_delay_base = 5
            monkeypatch.setattr(config, "LAMBDA_RETRY_BASE_DELAY_SECONDS", test_delay_base)

        # setup
        queue_name = f"destination-queue-{short_uid()}"
        fn_name = f"retry-fn-{short_uid()}"
        message_id = f"retry-msg-{short_uid()}"
        snapshot.add_transformer(snapshot.transform.regex(message_id, "<test-msg-id>"))

        queue_url = sqs_create_queue(QueueName=queue_name)
        queue_arn = sqs_get_queue_arn(queue_url)

        create_lambda_function(
            handler_file=os.path.join(os.path.dirname(__file__), "functions/lambda_echofail.py"),
            func_name=fn_name,
            runtime=Runtime.python3_12,
            role=lambda_su_role,
        )
        aws_client.lambda_.put_function_event_invoke_config(
            FunctionName=fn_name,
            MaximumRetryAttempts=2,
            DestinationConfig={"OnFailure": {"Destination": queue_arn}},
        )
        aws_client.lambda_.get_waiter("function_updated_v2").wait(FunctionName=fn_name)

        invoke_result = aws_client.lambda_.invoke(
            FunctionName=fn_name,
            Payload=to_bytes(json.dumps({"message": message_id})),
            InvocationType="Event",  # important, otherwise destinations won't be triggered
        )
        assert 200 <= invoke_result["StatusCode"] < 300

        def get_filtered_event_count() -> int:
            filter_result = retry(
                aws_client.logs.filter_log_events, sleep=2.0, logGroupName=f"/aws/lambda/{fn_name}"
            )
            filtered_log_events = [e for e in filter_result["events"] if message_id in e["message"]]
            return len(filtered_log_events)

        # between 0 and 1 min the lambda should NOT have been retried yet
        # between 1 min and 3 min the lambda should have been retried once
        # TODO: parse log and calculate time diffs for better/more reliable matching
        # SQS queue has a thread checking every second, hence we need a 1 second offset
        test_delay_base_with_offset = test_delay_base + 1
        time.sleep(test_delay_base_with_offset / 2)
        assert get_filtered_event_count() == 1
        time.sleep(test_delay_base_with_offset)
        assert get_filtered_event_count() == 2
        time.sleep(test_delay_base_with_offset * 2)
        assert get_filtered_event_count() == 3

        # 1. event should be in queue
        def msg_in_queue():
            msgs = aws_client.sqs.receive_message(
                QueueUrl=queue_url, AttributeNames=["All"], VisibilityTimeout=0
            )
            return len(msgs["Messages"]) == 1

        assert wait_until(msg_in_queue)

        # We didn't delete the message so it should be available again after waiting shortly (2x visibility timeout to be sure)
        msgs = aws_client.sqs.receive_message(
            QueueUrl=queue_url, AttributeNames=["All"], VisibilityTimeout=1
        )
        snapshot.match("queue_destination_payload", msgs)

        # 2. there should be only one event stream (re-use of environment)
        #    technically not guaranteed but should be nearly 100%
        log_streams = aws_client.logs.describe_log_streams(logGroupName=f"/aws/lambda/{fn_name}")
        assert len(log_streams["logStreams"]) == 1

        # 3. the lambda should have been called 3 times (correlation via custom message id)
        assert get_filtered_event_count() == 3

        # verify the event ID is the same in all calls
        log_events = aws_client.logs.filter_log_events(logGroupName=f"/aws/lambda/{fn_name}")[
            "events"
        ]

        # only get messages with the printed event
        request_ids = [
            json.loads(e["message"])["aws_request_id"]
            for e in log_events
            if message_id in e["message"]
        ]

        assert len(request_ids) == 3  # gather invocation ID from all 3 invocations
        assert len(set(request_ids)) == 1