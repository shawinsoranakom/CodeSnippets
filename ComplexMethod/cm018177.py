async def test_robot_with_no_update(
    hass: HomeAssistant, mock_account_with_litterrobot_4: MagicMock
) -> None:
    """Tests the update entity was set up."""
    robot: LitterRobot4 = mock_account_with_litterrobot_4.robots[0]
    robot.has_firmware_update = AsyncMock(return_value=False)
    robot.get_latest_firmware = AsyncMock(return_value=None)

    entry = await setup_integration(
        hass, mock_account_with_litterrobot_4, UPDATE_DOMAIN
    )

    state = hass.states.get(ENTITY_ID)
    assert state
    assert state.state == STATE_OFF
    assert state.attributes[ATTR_DEVICE_CLASS] == UpdateDeviceClass.FIRMWARE
    assert state.attributes[ATTR_INSTALLED_VERSION] == OLD_FIRMWARE
    assert state.attributes[ATTR_LATEST_VERSION] == OLD_FIRMWARE
    assert state.attributes[ATTR_RELEASE_URL] == RELEASE_URL

    assert await hass.config_entries.async_unload(entry.entry_id)
    await hass.async_block_till_done()