async def test_update_firmware(
    mock_sleep: MagicMock,
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_config_entry: MockConfigEntry,
    mock_smlight_client: MagicMock,
) -> None:
    """Test firmware updates."""
    await setup_integration(hass, mock_config_entry)
    entity_id = "update.mock_title_core_firmware"
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_INSTALLED_VERSION] == "v2.3.6"
    assert state.attributes[ATTR_LATEST_VERSION] == "v2.7.5"

    await hass.services.async_call(
        UPDATE_DOMAIN,
        SERVICE_INSTALL,
        {ATTR_ENTITY_ID: entity_id},
        blocking=False,
    )

    assert len(mock_smlight_client.fw_update.mock_calls) == 1

    event_function = get_mock_event_function(mock_smlight_client, SmEvents.ZB_FW_prgs)

    event_function(MOCK_FIRMWARE_PROGRESS)
    state = hass.states.get(entity_id)
    assert state.attributes[ATTR_IN_PROGRESS] is True
    assert state.attributes[ATTR_UPDATE_PERCENTAGE] == 50

    event_function = get_mock_event_function(mock_smlight_client, SmEvents.FW_UPD_done)

    event_function(MOCK_FIRMWARE_DONE)

    mock_smlight_client.get_info.side_effect = None
    mock_smlight_client.get_info.return_value = Info(
        sw_version="v2.7.5",
    )

    freezer.tick(timedelta(seconds=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_INSTALLED_VERSION] == "v2.7.5"
    assert state.attributes[ATTR_LATEST_VERSION] == "v2.7.5"