async def test_webhook_sensor_alarm_unset(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    hass_client_no_auth: ClientSessionGenerator,
) -> None:
    """Test unsetting sensors if there is no next alarm."""

    config_entry.add_to_hass(hass)
    await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    client = await hass_client_no_auth()

    response = await client.post(
        "/api/webhook/webhook_id",
        json={
            "event": "alarm_rescheduled",
            "value1": "1582719660934",
            "value2": "label",
        },
    )
    assert response.status == HTTPStatus.NO_CONTENT

    assert (state := hass.states.get("sensor.sleep_as_android_next_alarm"))
    assert state.state == "2020-02-26T12:21:00+00:00"

    assert (state := hass.states.get("sensor.sleep_as_android_alarm_label"))
    assert state.state == "label"

    response = await client.post(
        "/api/webhook/webhook_id",
        json={"event": "alarm_rescheduled"},
    )
    assert (state := hass.states.get("sensor.sleep_as_android_next_alarm"))
    assert state.state == STATE_UNKNOWN

    assert (state := hass.states.get("sensor.sleep_as_android_alarm_label"))
    assert state.state == STATE_UNKNOWN