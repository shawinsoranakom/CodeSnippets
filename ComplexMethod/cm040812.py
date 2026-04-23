def events_handler_put_events(self):
    entries = self._get_param("Entries")

    # keep track of events for local integration testing
    if config.is_local_test_mode():
        TEST_EVENTS_CACHE.extend(entries)

    events = [{"event": event, "uuid": str(long_uid())} for event in entries]

    _dump_events_to_files(events)

    for event_envelope in events:
        event = event_envelope["event"]
        event_bus_name = get_event_bus_name(event.get("EventBusName"))
        event_bus = self.events_backend.event_buses.get(event_bus_name)
        if not event_bus:
            continue

        matching_rules = [
            r
            for r in event_bus.rules.values()
            if r.event_bus_name == event_bus_name and not r.scheduled_expression
        ]
        if not matching_rules:
            continue

        event_time = datetime.datetime.utcnow()
        if event_timestamp := event.get("Time"):
            try:
                # if provided, use the time from event
                event_time = datetime.datetime.utcfromtimestamp(event_timestamp)
            except ValueError:
                # if we can't parse it, pass and keep using `utcnow`
                LOG.debug(
                    "Could not parse the `Time` parameter, falling back to `utcnow` for the following Event: '%s'",
                    event,
                )

        # See https://docs.aws.amazon.com/AmazonS3/latest/userguide/ev-events.html
        formatted_event = {
            "version": "0",
            "id": event_envelope["uuid"],
            "detail-type": event.get("DetailType"),
            "source": event.get("Source"),
            "account": self.current_account,
            "time": event_time.strftime("%Y-%m-%dT%H:%M:%SZ"),
            "region": self.region,
            "resources": event.get("Resources", []),
            "detail": json.loads(event.get("Detail", "{}")),
        }

        targets = []
        for rule in matching_rules:
            if filter_event_based_on_event_format(self, rule.name, event_bus_name, formatted_event):
                rule_targets, _ = self.events_backend.list_targets_by_rule(
                    rule.name, event_bus_arn(event_bus_name, self.current_account, self.region)
                )
                targets.extend([{"RuleArn": rule.arn} | target for target in rule_targets])
        # process event
        process_events(formatted_event, targets)

    content = {
        "FailedEntryCount": 0,  # TODO: dynamically set proper value when refactoring
        "Entries": [{"EventId": event["uuid"]} for event in events],
    }

    self.response_headers.update(
        {"Content-Type": APPLICATION_AMZ_JSON_1_1, "x-amzn-RequestId": short_uid()}
    )

    return json.dumps(content), self.response_headers