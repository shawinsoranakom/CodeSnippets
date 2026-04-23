def test_reserved_concurrency_async_queue(
        self,
        create_lambda_function,
        sqs_create_queue,
        sqs_collect_messages,
        snapshot,
        aws_client,
        aws_client_no_retry,
    ):
        """Test async/event invoke retry behavior due to limited reserved concurrency.
        Timeline:
        1) Set ReservedConcurrentExecutions=1
        2) sync_invoke_warm_up => ok
        3) async_invoke_one => ok
        4) async_invoke_two => gets retried
        5) sync invoke => fails with TooManyRequestsException
        6) Set ReservedConcurrentExecutions=3
        7) sync_invoke_final => ok
        """
        min_concurrent_executions = 10 + 3
        check_concurrency_quota(aws_client, min_concurrent_executions)

        queue_url = sqs_create_queue()

        func_name = f"test_lambda_{short_uid()}"
        create_lambda_function(
            func_name=func_name,
            handler_file=TEST_LAMBDA_NOTIFIER,
            runtime=Runtime.python3_12,
            client=aws_client.lambda_,
            timeout=30,
        )

        fn = aws_client.lambda_.get_function_configuration(
            FunctionName=func_name, Qualifier="$LATEST"
        )
        snapshot.match("fn", fn)
        fn_arn = fn["FunctionArn"]

        # configure reserved concurrency for sequential execution
        put_fn_concurrency = aws_client.lambda_.put_function_concurrency(
            FunctionName=func_name, ReservedConcurrentExecutions=1
        )
        snapshot.match("put_fn_concurrency", put_fn_concurrency)

        # warm up the Lambda function to mitigate flakiness due to cold start
        sync_invoke_warm_up = aws_client.lambda_.invoke(
            FunctionName=fn_arn, InvocationType="RequestResponse"
        )
        assert "FunctionError" not in sync_invoke_warm_up

        # Immediately queue two event invocations:
        # 1) The first event invoke gets executed immediately
        async_invoke_one = aws_client.lambda_.invoke(
            FunctionName=fn_arn,
            InvocationType="Event",
            Payload=json.dumps({"notify": queue_url, "wait": 15}),
        )
        assert "FunctionError" not in async_invoke_one
        # 2) The second event invoke gets throttled and re-scheduled with an internal retry
        async_invoke_two = aws_client.lambda_.invoke(
            FunctionName=fn_arn,
            InvocationType="Event",
            Payload=json.dumps({"notify": queue_url}),
        )
        assert "FunctionError" not in async_invoke_two

        # Wait until the first async invoke is being executed while the second async invoke is in the queue.
        messages = sqs_collect_messages(
            queue_url,
            expected=1,
            timeout=15,
        )
        async_invoke_one_notification = json.loads(messages[0]["Body"])
        assert (
            async_invoke_one_notification["request_id"]
            == async_invoke_one["ResponseMetadata"]["RequestId"]
        )

        # Synchronous invocations raise an exception because insufficient reserved concurrency is available
        # It is important to disable botocore retries because the concurrency limit is time-bound because it only
        # triggers as long as the first async invoke is processing!
        with pytest.raises(aws_client.lambda_.exceptions.TooManyRequestsException) as e:
            aws_client_no_retry.lambda_.invoke(
                FunctionName=fn_arn, InvocationType="RequestResponse"
            )
        snapshot.match("too_many_requests_exc", e.value.response)

        # ReservedConcurrentExecutions=2 is insufficient because the throttled async event invoke might be
        # re-scheduled before the synchronous invoke while the first async invoke is still running.
        aws_client.lambda_.put_function_concurrency(
            FunctionName=func_name, ReservedConcurrentExecutions=3
        )
        # Invocations succeed after raising reserved concurrency
        sync_invoke_final = aws_client.lambda_.invoke(
            FunctionName=fn_arn,
            InvocationType="RequestResponse",
            Payload=json.dumps({"notify": queue_url}),
        )
        assert "FunctionError" not in sync_invoke_final

        # Contains the re-queued `async_invoke_two` and the `sync_invoke_final`, but the order might differ
        # depending on whether invoke_two gets re-schedule before or after the final invoke.
        # AWS docs: https://docs.aws.amazon.com/lambda/latest/dg/invocation-async-error-handling.html
        # "The retry interval increases exponentially from 1 second after the first attempt to a maximum of 5 minutes."
        final_messages = sqs_collect_messages(
            queue_url,
            expected=2,
            timeout=20,
        )
        invoked_request_ids = {json.loads(msg["Body"])["request_id"] for msg in final_messages}
        assert {
            async_invoke_two["ResponseMetadata"]["RequestId"],
            sync_invoke_final["ResponseMetadata"]["RequestId"],
        } == invoked_request_ids