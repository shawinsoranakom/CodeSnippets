def test_recreate_tagged_resource_without_tags(
    event_bus_name,
    resource_to_tag,
    region_name,
    account_id,
    events_create_event_bus,
    events_put_rule,
    aws_client,
    snapshot,
):
    if event_bus_name == "event_bus_default":
        bus_name = "default"
        event_bus_arn = f"arn:aws:events:{region_name}:{account_id}:event-bus/default"
    if event_bus_name == "event_bus_custom":
        bus_name = f"test_bus-{short_uid()}"
        response = events_create_event_bus(Name=bus_name)
        event_bus_arn = response["EventBusArn"]

    if resource_to_tag == "event_bus":
        resource_arn = event_bus_arn
    if resource_to_tag == "rule":
        rule_name = f"test_rule-{short_uid()}"
        response = events_put_rule(
            Name=rule_name,
            EventBusName=bus_name,
            EventPattern=json.dumps(TEST_EVENT_PATTERN),
        )
        rule_arn = response["RuleArn"]
        resource_arn = rule_arn

    aws_client.events.tag_resource(
        ResourceARN=resource_arn,
        Tags=[
            {
                "Key": "tag1",
                "Value": "value1",
            }
        ],
    )

    if resource_to_tag == "event_bus" and event_bus_name == "event_bus_custom":
        aws_client.events.delete_event_bus(Name=bus_name)
        events_create_event_bus(Name=bus_name)

    if resource_to_tag == "rule":
        aws_client.events.delete_rule(Name=rule_name, EventBusName=bus_name)
        events_put_rule(
            Name=rule_name,
            EventBusName=bus_name,
            EventPattern=json.dumps(TEST_EVENT_PATTERN),
        )

    response = aws_client.events.list_tags_for_resource(ResourceARN=resource_arn)
    snapshot.match("list_tags_for_resource", response)