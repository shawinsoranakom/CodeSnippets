def _put_events_with_filter_to_sqs(
        pattern: dict,
        entries_asserts: list[tuple[list[dict], bool]],
        event_bus_name: str = None,
        input_path: str = None,
        input_transformer: dict[dict, str] = None,
    ):
        rule_name = f"test-rule-{short_uid()}"
        target_id = f"test-target-{short_uid()}"
        if not event_bus_name:
            event_bus_name = f"test-bus-{short_uid()}"
            events_create_event_bus(Name=event_bus_name)

        queue_url, queue_arn, _ = sqs_as_events_target()

        events_put_rule(
            Name=rule_name,
            EventBusName=event_bus_name,
            EventPattern=json.dumps(pattern),
        )

        kwargs = {"InputPath": input_path} if input_path else {}
        if input_transformer:
            kwargs["InputTransformer"] = input_transformer

        response = aws_client.events.put_targets(
            Rule=rule_name,
            EventBusName=event_bus_name,
            Targets=[{"Id": target_id, "Arn": queue_arn, **kwargs}],
        )

        assert response["FailedEntryCount"] == 0
        assert response["FailedEntries"] == []

        messages = []
        for entry_asserts in entries_asserts:
            entries = entry_asserts[0]
            for entry in entries:
                entry["EventBusName"] = event_bus_name
            message = put_entries_assert_results_sqs(
                aws_client.events,
                aws_client.sqs,
                queue_url,
                entries=entries,
                should_match=entry_asserts[1],
            )
            if message is not None:
                messages.extend(message)

        return messages