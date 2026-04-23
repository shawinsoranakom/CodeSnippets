def events_create_event_bus(aws_client, region_name, account_id):
    event_bus_names = []

    def _create_event_bus(**kwargs):
        if "Name" not in kwargs:
            kwargs["Name"] = f"test-event-bus-{short_uid()}"

        response = aws_client.events.create_event_bus(**kwargs)
        event_bus_names.append(kwargs["Name"])
        return response

    yield _create_event_bus

    for event_bus_name in event_bus_names:
        try:
            response = aws_client.events.list_rules(EventBusName=event_bus_name)
            rules = [rule["Name"] for rule in response["Rules"]]

            # Delete all rules for the current event bus
            for rule in rules:
                try:
                    response = aws_client.events.list_targets_by_rule(
                        Rule=rule, EventBusName=event_bus_name
                    )
                    targets = [target["Id"] for target in response["Targets"]]

                    # Remove all targets for the current rule
                    if targets:
                        for target in targets:
                            aws_client.events.remove_targets(
                                Rule=rule, EventBusName=event_bus_name, Ids=[target]
                            )

                    aws_client.events.delete_rule(Name=rule, EventBusName=event_bus_name)
                except Exception as e:
                    LOG.warning("Failed to delete rule %s: %s", rule, e)

            # Delete archives for event bus
            event_source_arn = (
                f"arn:aws:events:{region_name}:{account_id}:event-bus/{event_bus_name}"
            )
            response = aws_client.events.list_archives(EventSourceArn=event_source_arn)
            archives = [archive["ArchiveName"] for archive in response["Archives"]]
            for archive in archives:
                try:
                    aws_client.events.delete_archive(ArchiveName=archive)
                except Exception as e:
                    LOG.warning("Failed to delete archive %s: %s", archive, e)

            aws_client.events.delete_event_bus(Name=event_bus_name)
        except Exception as e:
            LOG.warning("Failed to delete event bus %s: %s", event_bus_name, e)