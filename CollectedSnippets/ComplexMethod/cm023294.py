async def test_update_entity_reload(
    hass: HomeAssistant,
    client: MagicMock,
    climate_radio_thermostat_ct100_plus_different_endpoints: Node,
    integration: MockConfigEntry,
    entity_id: str,
    installed_version: str,
) -> None:
    """Test update entity maintains state after reload."""
    config_entry = integration
    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF

    client.async_send_command.return_value = {"updates": []}

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=15, days=1))
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF

    client.async_send_command.return_value = FIRMWARE_UPDATES

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=15, days=2))
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_ON
    attrs = state.attributes
    assert not attrs[ATTR_AUTO_UPDATE]
    assert attrs[ATTR_INSTALLED_VERSION] == installed_version
    assert attrs[ATTR_IN_PROGRESS] is False
    assert attrs[ATTR_UPDATE_PERCENTAGE] is None
    assert attrs[ATTR_LATEST_VERSION] == "11.2.4"
    assert attrs[ATTR_RELEASE_URL] is None

    await hass.services.async_call(
        UPDATE_DOMAIN,
        SERVICE_SKIP,
        {
            ATTR_ENTITY_ID: entity_id,
        },
        blocking=True,
    )

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_SKIPPED_VERSION] == "11.2.4"

    await hass.config_entries.async_reload(config_entry.entry_id)
    await hass.async_block_till_done()

    # Trigger another update and make sure the skipped version is still skipped
    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=15, days=4))
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_SKIPPED_VERSION] == "11.2.4"