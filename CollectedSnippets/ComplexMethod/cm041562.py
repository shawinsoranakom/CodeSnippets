def _assert(expected_len):
        rs = aws_client.events.list_event_buses()
        event_buses = [eb for eb in rs["EventBuses"] if eb["Name"] == "my-test-bus"]
        assert len(event_buses) == expected_len
        rs = aws_client.events.list_connections()
        connections = [con for con in rs["Connections"] if con["Name"] == "my-test-conn"]
        assert len(connections) == expected_len
        rs = aws_client.events.list_api_destinations()
        api_destinations = [
            ad for ad in rs["ApiDestinations"] if ad["Name"] == "my-test-destination"
        ]
        assert len(api_destinations) == expected_len