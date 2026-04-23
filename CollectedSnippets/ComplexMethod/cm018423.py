async def test_fetch_period_api_with_minimal_response(
    hass: HomeAssistant, hass_client: ClientSessionGenerator
) -> None:
    """Test the fetch period view for history with minimal_response."""
    now = dt_util.utcnow()
    await async_setup_component(hass, "history", {})

    hass.states.async_set("sensor.power", 0, {"attr": "any"})
    await async_wait_recording_done(hass)
    hass.states.async_set("sensor.power", 50, {"attr": "any"})
    await async_wait_recording_done(hass)
    hass.states.async_set("sensor.power", 23, {"attr": "any"})
    last_changed = hass.states.get("sensor.power").last_changed
    await async_wait_recording_done(hass)
    hass.states.async_set("sensor.power", 23, {"attr": "any"})
    await async_wait_recording_done(hass)
    client = await hass_client()
    response = await client.get(
        f"/api/history/period/{now.isoformat()}?filter_entity_id=sensor.power&minimal_response&no_attributes"
    )
    assert response.status == HTTPStatus.OK
    response_json = await response.json()
    assert len(response_json[0]) == 3
    state_list = response_json[0]

    assert state_list[0]["entity_id"] == "sensor.power"
    assert state_list[0]["attributes"] == {}
    assert state_list[0]["state"] == "0"

    assert "attributes" not in state_list[1]
    assert "entity_id" not in state_list[1]
    assert state_list[1]["state"] == "50"

    assert "attributes" not in state_list[2]
    assert "entity_id" not in state_list[2]
    assert state_list[2]["state"] == "23"
    assert state_list[2]["last_changed"] == json.dumps(
        process_timestamp(last_changed),
        cls=JSONEncoder,
    ).replace('"', "")