async def test_robot_with_update_already_in_progress(
    hass: HomeAssistant, mock_account_with_litterrobot_4: MagicMock
) -> None:
    """Tests the update entity was set up."""
    robot: LitterRobot4 = mock_account_with_litterrobot_4.robots[0]
    robot._update_data({"isFirmwareUpdateTriggered": True}, partial=True)

    entry = await setup_integration(
        hass, mock_account_with_litterrobot_4, UPDATE_DOMAIN
    )

    state = hass.states.get(ENTITY_ID)
    assert state
    assert state.state == STATE_UNKNOWN
    assert state.attributes[ATTR_DEVICE_CLASS] == UpdateDeviceClass.FIRMWARE
    assert state.attributes[ATTR_INSTALLED_VERSION] == OLD_FIRMWARE
    assert state.attributes[ATTR_LATEST_VERSION] is None
    assert state.attributes[ATTR_RELEASE_URL] == RELEASE_URL

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()