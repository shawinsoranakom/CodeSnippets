def test_whitebox_create_analytics_payload():
    agg = ServiceRequestAggregator()

    agg.add_request(ServiceRequestInfo("test1", "test", 200, None))
    agg.add_request(ServiceRequestInfo("test1", "test", 200, None))
    agg.add_request(ServiceRequestInfo("test2", "test", 404, "ResourceNotFound"))
    agg.add_request(ServiceRequestInfo("test3", "test", 200, None))

    payload = agg._create_analytics_payload()

    aggregations = payload["api_calls"]
    assert len(aggregations) == 3

    period_start = dateutil.parser.isoparse(payload["period_start_time"])
    period_end = dateutil.parser.isoparse(payload["period_end_time"])
    assert period_end > period_start

    for record in aggregations:
        service = record["service"]
        if service == "test1":
            assert record["count"] == 2
            assert "err_type" not in record
        elif service == "test2":
            assert record["count"] == 1
            assert record["err_type"] == "ResourceNotFound"
        elif service == "test3":
            assert record["count"] == 1
            assert "err_type" not in record
        else:
            pytest.fail(f"unexpected service name in payload: '{service}'")