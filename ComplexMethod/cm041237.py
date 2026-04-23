def _clean_up(
        bus_name=None,
        rule_name=None,
        target_ids=None,
        queue_url=None,
        log_group_name=None,
    ):
        events_client = aws_client.events
        kwargs = {"EventBusName": bus_name} if bus_name else {}
        if target_ids:
            target_ids = target_ids if isinstance(target_ids, list) else [target_ids]
            call_safe(
                events_client.remove_targets,
                kwargs=dict(Rule=rule_name, Ids=target_ids, Force=True, **kwargs),
            )
        if rule_name:
            call_safe(events_client.delete_rule, kwargs=dict(Name=rule_name, Force=True, **kwargs))
        if bus_name:
            call_safe(events_client.delete_event_bus, kwargs={"Name": bus_name})
        if queue_url:
            sqs_client = aws_client.sqs
            call_safe(sqs_client.delete_queue, kwargs={"QueueUrl": queue_url})
        if log_group_name:
            logs_client = aws_client.logs

            def _delete_log_group():
                log_streams = logs_client.describe_log_streams(logGroupName=log_group_name)
                for log_stream in log_streams["logStreams"]:
                    logs_client.delete_log_stream(
                        logGroupName=log_group_name, logStreamName=log_stream["logStreamName"]
                    )
                logs_client.delete_log_group(logGroupName=log_group_name)

            call_safe(_delete_log_group)