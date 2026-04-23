async def test_generic_device_update_entity_has_update(
    hass: HomeAssistant,
    mock_client: APIClient,
    mock_esphome_device: MockESPHomeDeviceType,
) -> None:
    """Test a generic device update entity with an update."""
    entity_info = [
        UpdateInfo(
            object_id="myupdate",
            key=1,
            name="my update",
        )
    ]
    states = [
        UpdateState(
            key=1,
            current_version="2024.6.0",
            latest_version="2024.6.1",
            title="ESPHome Project",
            release_summary=RELEASE_SUMMARY,
            release_url=RELEASE_URL,
        )
    ]
    mock_device = await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        states=states,
    )
    state = hass.states.get(ENTITY_ID)
    assert state is not None
    assert state.state == STATE_ON

    await hass.services.async_call(
        UPDATE_DOMAIN,
        SERVICE_INSTALL,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )

    mock_device.set_state(
        UpdateState(
            key=1,
            in_progress=True,
            has_progress=True,
            progress=50,
            current_version="2024.6.0",
            latest_version="2024.6.1",
            title="ESPHome Project",
            release_summary=RELEASE_SUMMARY,
            release_url=RELEASE_URL,
        )
    )

    state = hass.states.get(ENTITY_ID)
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes[ATTR_IN_PROGRESS] is True
    assert state.attributes[ATTR_UPDATE_PERCENTAGE] == 50
    await hass.services.async_call(
        HOMEASSISTANT_DOMAIN,
        SERVICE_UPDATE_ENTITY,
        {ATTR_ENTITY_ID: ENTITY_ID},
        blocking=True,
    )

    mock_device.set_state(
        UpdateState(
            key=1,
            in_progress=True,
            has_progress=False,
            current_version="2024.6.0",
            latest_version="2024.6.1",
            title="ESPHome Project",
            release_summary=RELEASE_SUMMARY,
            release_url=RELEASE_URL,
        )
    )

    state = hass.states.get(ENTITY_ID)
    assert state is not None
    assert state.state == STATE_ON
    assert state.attributes[ATTR_IN_PROGRESS] is True
    assert state.attributes[ATTR_UPDATE_PERCENTAGE] is None

    mock_client.update_command.assert_called_with(
        key=1, command=UpdateCommand.CHECK, device_id=0
    )