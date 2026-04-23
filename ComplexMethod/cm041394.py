def test_integration(monkeypatch):
    events: list[Event] = []

    def _handle(_event: Event):
        events.append(_event)

    monkeypatch.setattr(analytics.log.handler, "handle", _handle)

    agg = ServiceRequestAggregator(flush_interval=1)

    agg.add_request(ServiceRequestInfo("s3", "ListBuckets", 200))
    agg.add_request(ServiceRequestInfo("s3", "CreateBucket", 200))
    agg.add_request(ServiceRequestInfo("s3", "HeadBucket", 200))
    agg.add_request(ServiceRequestInfo("s3", "HeadBucket", 200))

    agg.start()
    time.sleep(1.2)

    assert len(events) == 1, f"expected events to be flushed {events}"

    agg.add_request(ServiceRequestInfo("s3", "HeadBucket", 404))
    agg.add_request(ServiceRequestInfo("s3", "CreateBucket", 200))
    agg.add_request(ServiceRequestInfo("s3", "HeadBucket", 200))

    assert len(events) == 1, f"did not expect events to be flushed {events}"

    agg.shutdown()  # should flush

    assert len(events) == 2, f"expected events to be flushed {events}"

    event = events[0]
    assert event.name == EVENT_NAME
    calls = event.payload["api_calls"]
    assert {"count": 1, "operation": "ListBuckets", "service": "s3", "status_code": 200} in calls
    assert {"count": 1, "operation": "CreateBucket", "service": "s3", "status_code": 200} in calls
    assert {"count": 2, "operation": "HeadBucket", "service": "s3", "status_code": 200} in calls

    event = events[1]
    assert event.name == EVENT_NAME
    calls = event.payload["api_calls"]
    assert {"count": 1, "operation": "CreateBucket", "service": "s3", "status_code": 200} in calls
    assert {"count": 1, "operation": "HeadBucket", "service": "s3", "status_code": 200} in calls
    assert {"count": 1, "operation": "HeadBucket", "service": "s3", "status_code": 404} in calls