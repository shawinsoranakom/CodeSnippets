def test_event_rules_deployed(self, aws_client, setup_and_teardown):
        events = aws_client.events
        rules = events.list_rules()["Rules"]

        rule = ([r for r in rules if r["Name"] == "sls-test-cf-event"] or [None])[0]
        assert rule
        assert "Arn" in rule
        pattern = json.loads(rule["EventPattern"])
        assert ["aws.cloudformation"] == pattern["source"]
        assert "detail-type" in pattern

        event_bus_name = "customBus"
        rule = events.list_rules(EventBusName=event_bus_name)["Rules"][0]
        assert rule
        assert {"source": ["customSource"]} == json.loads(rule["EventPattern"])