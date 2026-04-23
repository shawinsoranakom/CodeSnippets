def test_xray_trace_propagation_events_events(
    bus_combination,
    create_lambda_function,
    events_create_event_bus,
    create_role_event_bus_source_to_bus_target,
    region_name,
    account_id,
    events_put_rule,
    cleanups,
    aws_client,
):
    """
    Event Bridge Bus Source to Event Bridge Bus Target to Lambda for asserting X-Ray trace propagation
    """
    # Create event buses
    bus_source, bus_target = bus_combination
    if bus_source == "default":
        bus_name_source = "default"
    if bus_source == "custom":
        bus_name_source = f"test-event-bus-source-{short_uid()}"
        events_create_event_bus(Name=bus_name_source)
    if bus_target == "default":
        bus_name_target = "default"
        bus_arn_target = f"arn:aws:events:{region_name}:{account_id}:event-bus/default"
    if bus_target == "custom":
        bus_name_target = f"test-event-bus-target-{short_uid()}"
        bus_arn_target = events_create_event_bus(Name=bus_name_target)["EventBusArn"]

    # Create permission for event bus source to send events to event bus target
    role_arn_bus_source_to_bus_target = create_role_event_bus_source_to_bus_target()

    if is_aws_cloud():
        time.sleep(10)  # required for role propagation

    # Permission for event bus target to receive events from event bus source
    aws_client.events.put_permission(
        StatementId=f"TargetEventBusAccessPermission{short_uid()}",
        EventBusName=bus_name_target,
        Action="events:PutEvents",
        Principal="*",
    )

    # Create rule source event bus to target
    rule_name_source_to_target = f"test-rule-source-to-target-{short_uid()}"
    events_put_rule(
        Name=rule_name_source_to_target,
        EventBusName=bus_name_source,
        EventPattern=json.dumps(TEST_EVENT_PATTERN),
    )

    # Add target event bus as target
    target_id_event_bus_target = f"test-target-source-events-{short_uid()}"
    aws_client.events.put_targets(
        Rule=rule_name_source_to_target,
        EventBusName=bus_name_source,
        Targets=[
            {
                "Id": target_id_event_bus_target,
                "Arn": bus_arn_target,
                "RoleArn": role_arn_bus_source_to_bus_target,
            }
        ],
    )

    # Create Lambda function
    function_name = f"lambda-func-{short_uid()}"
    create_lambda_response = create_lambda_function(
        handler_file=TEST_LAMBDA_XRAY_TRACEID,
        func_name=function_name,
        runtime=Runtime.python3_12,
    )
    lambda_function_arn = create_lambda_response["CreateFunctionResponse"]["FunctionArn"]

    # Connect Event Bus Target to Lambda
    rule_name_lambda = f"rule-{short_uid()}"
    rule_arn_lambda = events_put_rule(
        Name=rule_name_lambda,
        EventBusName=bus_name_target,
        EventPattern=json.dumps(TEST_EVENT_PATTERN),
    )["RuleArn"]

    aws_client.lambda_.add_permission(
        FunctionName=function_name,
        StatementId=f"{rule_name_lambda}-Event",
        Action="lambda:InvokeFunction",
        Principal="events.amazonaws.com",
        SourceArn=rule_arn_lambda,
    )

    target_id_lambda = f"target-{short_uid()}"
    aws_client.events.put_targets(
        Rule=rule_name_lambda,
        EventBusName=bus_name_target,
        Targets=[{"Id": target_id_lambda, "Arn": lambda_function_arn}],
    )

    ######
    # Test
    ######

    # Enable X-Ray tracing for the aws_client
    trace_id = "1-67f4141f-e1cd7672871da115129f8b19"
    parent_id = "d0ee9531727135a0"
    xray_trace_header = TraceHeader(root=trace_id, parent=parent_id, sampled=1)

    def add_xray_header(request, **kwargs):
        request.headers["X-Amzn-Trace-Id"] = xray_trace_header.to_header_str()

    event_name = "before-send.events.*"
    aws_client.events.meta.events.register(event_name, add_xray_header)
    # make sure the hook gets cleaned up after the test
    cleanups.append(lambda: aws_client.events.meta.events.unregister(event_name, add_xray_header))

    aws_client.events.put_events(
        Entries=[
            {
                "EventBusName": bus_name_source,
                "Source": TEST_EVENT_PATTERN["source"][0],
                "DetailType": TEST_EVENT_PATTERN["detail-type"][0],
                "Detail": json.dumps(TEST_EVENT_DETAIL),
            }
        ]
    )

    # Verify the Lambda invocation
    events = retry(
        check_expected_lambda_log_events_length,
        retries=10,
        sleep=10,
        function_name=function_name,
        expected_length=1,
        logs_client=aws_client.logs,
    )

    # TODO how to assert X-Ray trace ID correct propagation from eventbridge to eventbridge lambda if no X-Ray trace id is present in the event

    lambda_trace_header = events[0]["trace_id_inside_handler"]
    assert lambda_trace_header is not None
    lambda_trace_id = re.search(r"Root=([^;]+)", lambda_trace_header).group(1)
    assert lambda_trace_id == trace_id