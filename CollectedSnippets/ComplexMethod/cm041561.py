def test_eventbus_policy_statement(deploy_cfn_template, aws_client):
    event_bus_name = f"event-bus-{short_uid()}"
    statement_id = f"statement-{short_uid()}"

    deploy_cfn_template(
        template_path=os.path.join(
            os.path.dirname(__file__), "../../../templates/eventbridge_policy_statement.yaml"
        ),
        parameters={"EventBusName": event_bus_name, "StatementId": statement_id},
    )

    describe_response = aws_client.events.describe_event_bus(Name=event_bus_name)
    policy = json.loads(describe_response["Policy"])
    assert policy["Version"] == "2012-10-17"
    assert len(policy["Statement"]) == 1
    statement = policy["Statement"][0]
    assert statement["Sid"] == statement_id
    assert statement["Action"] == "events:PutEvents"
    assert statement["Principal"] == "*"
    assert statement["Effect"] == "Allow"
    assert event_bus_name in statement["Resource"]