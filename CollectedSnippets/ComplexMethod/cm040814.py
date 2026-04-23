def func(*args, **kwargs):
            account_id = store._account_id
            region = store._region_name
            moto_backend = events_backends[account_id][region]
            event_bus_name = get_event_bus_name(event_bus_name_or_arn)
            event_bus = moto_backend.event_buses[event_bus_name]
            rule = event_bus.rules.get(rule_name)
            if not rule:
                LOG.info("Unable to find rule `%s` for event bus `%s`", rule_name, event_bus_name)
                return
            if rule.targets:
                LOG.debug(
                    "Notifying %s targets in response to triggered Events rule %s",
                    len(rule.targets),
                    rule_name,
                )

            default_event = {
                "version": "0",
                "id": long_uid(),
                "detail-type": "Scheduled Event",
                "source": "aws.events",
                "account": account_id,
                "time": timestamp(format=TIMESTAMP_FORMAT_TZ),
                "region": region,
                "resources": [rule.arn],
                "detail": {},
            }

            for target in rule.targets:
                arn = target.get("Arn")

                if input_ := target.get("Input"):
                    event = json.loads(input_)
                else:
                    event = default_event
                    if target.get("InputPath"):
                        event = filter_event_with_target_input_path(target, event)
                    if input_transformer := target.get("InputTransformer"):
                        event = process_event_with_input_transformer(input_transformer, event)

                attr = pick_attributes(target, ["$.SqsParameters", "$.KinesisParameters"])

                try:
                    send_event_to_target(
                        arn,
                        event,
                        target_attributes=attr,
                        role=target.get("RoleArn"),
                        target=target,
                        source_arn=rule.arn,
                        source_service=ServicePrincipal.events,
                    )
                except Exception as e:
                    LOG.info(
                        "Unable to send event notification %s to target %s: %s",
                        truncate(event),
                        target,
                        e,
                    )