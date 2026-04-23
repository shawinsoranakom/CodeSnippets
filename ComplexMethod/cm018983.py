async def test_update_zigbee2_firmware(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    mock_config_entry: MockConfigEntry,
    mock_smlight_client: MagicMock,
) -> None:
    """Test update of zigbee2 firmware where available."""
    mock_info = Info.from_dict(
        await async_load_json_object_fixture(hass, "info-MR1.json", DOMAIN)
    )
    mock_smlight_client.get_info.side_effect = None
    mock_smlight_client.get_info.return_value = mock_info
    await setup_integration(hass, mock_config_entry)
    entity_id = "update.mock_title_zigbee_firmware_2"
    state = hass.states.get(entity_id)
    assert state.state == STATE_ON
    assert state.attributes[ATTR_INSTALLED_VERSION] == "20240314"
    assert state.attributes[ATTR_LATEST_VERSION] == "20240716"

    await hass.services.async_call(
        UPDATE_DOMAIN,
        SERVICE_INSTALL,
        {ATTR_ENTITY_ID: entity_id},
        blocking=False,
    )

    assert len(mock_smlight_client.fw_update.mock_calls) == 1

    event_function = get_mock_event_function(mock_smlight_client, SmEvents.FW_UPD_done)

    event_function(MOCK_FIRMWARE_DONE)

    mock_info.radios[1] = MOCK_RADIO

    freezer.tick(timedelta(seconds=5))
    async_fire_time_changed(hass)
    await hass.async_block_till_done()

    state = hass.states.get(entity_id)
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_INSTALLED_VERSION] == "20240716"
    assert state.attributes[ATTR_LATEST_VERSION] == "20240716"