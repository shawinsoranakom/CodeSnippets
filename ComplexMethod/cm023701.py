async def test_lazy_state_handles_different_last_updated_and_last_changed(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test that the LazyState handles different last_updated and last_changed."""
    now = datetime(2021, 6, 12, 3, 4, 1, 323, tzinfo=dt_util.UTC)
    row = PropertyMock(
        entity_id="sensor.valid",
        state="off",
        attributes='{"shared":true}',
        last_updated_ts=now.timestamp(),
        last_reported_ts=now.timestamp(),
        last_changed_ts=(now - timedelta(seconds=60)).timestamp(),
    )
    lstate = LazyState(
        row, {}, None, row.entity_id, row.state, row.last_updated_ts, False
    )
    assert lstate.as_dict() == {
        "attributes": {"shared": True},
        "entity_id": "sensor.valid",
        "last_changed": "2021-06-12T03:03:01.000323+00:00",
        "last_updated": "2021-06-12T03:04:01.000323+00:00",
        "state": "off",
    }
    assert lstate.last_updated.timestamp() == row.last_updated_ts
    assert lstate.last_changed.timestamp() == row.last_changed_ts
    assert lstate.last_reported.timestamp() == row.last_updated_ts
    assert lstate.as_dict() == {
        "attributes": {"shared": True},
        "entity_id": "sensor.valid",
        "last_changed": "2021-06-12T03:03:01.000323+00:00",
        "last_updated": "2021-06-12T03:04:01.000323+00:00",
        "state": "off",
    }
    assert lstate.last_changed_timestamp == row.last_changed_ts
    assert lstate.last_updated_timestamp == row.last_updated_ts
    assert lstate.last_reported_timestamp == row.last_updated_ts