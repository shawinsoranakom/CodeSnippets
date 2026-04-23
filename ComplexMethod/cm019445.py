async def test_update_sensor(hass: HomeAssistant) -> None:
    """Test async_update for sensor."""
    assert hass.state is CoreState.running

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={CONF_HOST: HOST, CONF_PORT: PORT},
        unique_id=f"{HOST}:{PORT}",
    )

    starting_time = static_datetime()
    timestamp = future_timestamp(100)

    with (
        freeze_time(starting_time),
        patch(
            "homeassistant.components.cert_expiry.coordinator.get_cert_expiry_timestamp",
            return_value=timestamp,
        ),
    ):
        entry.add_to_hass(hass)
        assert await hass.config_entries.async_setup(entry.entry_id)
        await hass.async_block_till_done()

    state = hass.states.get("sensor.example_com_cert_expiry")
    assert state is not None
    assert state.state != STATE_UNAVAILABLE
    assert state.state == timestamp.isoformat()
    assert state.attributes.get("error") == "None"
    assert state.attributes.get("is_valid")

    next_update = starting_time + timedelta(hours=24)
    with (
        freeze_time(next_update),
        patch(
            "homeassistant.components.cert_expiry.coordinator.get_cert_expiry_timestamp",
            return_value=timestamp,
        ),
    ):
        async_fire_time_changed(hass, utcnow() + timedelta(hours=24))
        await hass.async_block_till_done()

    state = hass.states.get("sensor.example_com_cert_expiry")
    assert state is not None
    assert state.state != STATE_UNAVAILABLE
    assert state.state == timestamp.isoformat()
    assert state.attributes.get("error") == "None"
    assert state.attributes.get("is_valid")