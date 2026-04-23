def notify_event_destinations(
    context: RequestContext,
    # FIXME: Moto stores the Event Destinations as a single value when it should be a list
    event_destinations: EventDestination | list[EventDestination],
    payload: EventDestinationPayload,
    email_type: EmailType,
):
    emitter = SNSEmitter(context)

    if not isinstance(event_destinations, list):
        event_destinations = [event_destinations]

    for event_destination in event_destinations:
        if not event_destination["Enabled"]:
            continue

        sns_destination_arn = event_destination.get("SNSDestination", {}).get("TopicARN")
        if not sns_destination_arn:
            continue

        matching_event_types = event_destination.get("MatchingEventTypes") or []
        if EventType.send in matching_event_types:
            emitter.emit_send_event(
                payload, sns_destination_arn, emit_source_arn=email_type != EmailType.TEMPLATED
            )
        if EventType.delivery in matching_event_types:
            emitter.emit_delivery_event(payload, sns_destination_arn)