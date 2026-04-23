async def test_webhook_update_location_without_locations(
    hass: HomeAssistant,
    create_registrations: tuple[dict[str, Any], dict[str, Any]],
    webhook_client: TestClient,
) -> None:
    """Test that location can be updated."""

    # start off with a location set by name
    resp = await webhook_client.post(
        f"/api/webhook/{create_registrations[1]['webhook_id']}",
        json={
            "type": "update_location",
            "data": {"location_name": STATE_HOME},
        },
    )

    assert resp.status == HTTPStatus.OK

    state = hass.states.get("device_tracker.test_1_2")
    assert state is not None
    assert state.state == STATE_HOME

    # set location to an 'unknown' state
    resp = await webhook_client.post(
        f"/api/webhook/{create_registrations[1]['webhook_id']}",
        json={
            "type": "update_location",
            "data": {"altitude": 123},
        },
    )

    assert resp.status == HTTPStatus.OK

    state = hass.states.get("device_tracker.test_1_2")
    assert state is not None
    assert state.state == STATE_UNKNOWN
    assert state.attributes["altitude"] == 123