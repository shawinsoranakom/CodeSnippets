async def test_update_entity_progress(
    hass: HomeAssistant,
    client: MagicMock,
    climate_radio_thermostat_ct100_plus_different_endpoints: Node,
    integration: MockConfigEntry,
    entity_id: str,
    installed_version: str,
    install_result: dict[str, Any],
    progress_event: Event,
    finished_event: Event,
) -> None:
    """Test update entity progress."""
    client.async_send_command.return_value = FIRMWARE_UPDATES
    driver = client.driver

    async_fire_time_changed(hass, dt_util.utcnow() + timedelta(seconds=15, days=1))
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state
    assert state.state == STATE_ON
    attrs = state.attributes
    assert attrs[ATTR_INSTALLED_VERSION] == installed_version
    assert attrs[ATTR_LATEST_VERSION] == "11.2.4"

    client.async_send_command.reset_mock()
    client.async_send_command.return_value = {"result": install_result}

    # Test successful install call without a version
    install_task = hass.async_create_task(
        hass.services.async_call(
            UPDATE_DOMAIN,
            SERVICE_INSTALL,
            {
                ATTR_ENTITY_ID: entity_id,
            },
            blocking=True,
        )
    )

    # Sleep so that task starts
    await asyncio.sleep(0.05)

    state = hass.states.get(entity_id)
    assert state
    attrs = state.attributes
    assert attrs[ATTR_IN_PROGRESS] is True
    assert attrs[ATTR_UPDATE_PERCENTAGE] is None

    driver.receive_event(progress_event)
    await asyncio.sleep(0.05)

    # Validate that the progress is updated
    state = hass.states.get(entity_id)
    assert state
    attrs = state.attributes
    assert attrs[ATTR_IN_PROGRESS] is True
    assert attrs[ATTR_UPDATE_PERCENTAGE] == 5

    driver.receive_event(finished_event)
    await hass.async_block_till_done()

    # Validate that progress is reset and entity reflects new version
    state = hass.states.get(entity_id)
    assert state
    attrs = state.attributes
    assert attrs[ATTR_IN_PROGRESS] is False
    assert attrs[ATTR_UPDATE_PERCENTAGE] is None
    assert attrs[ATTR_INSTALLED_VERSION] == "11.2.4"
    assert attrs[ATTR_LATEST_VERSION] == "11.2.4"
    assert state.state == STATE_OFF

    await install_task