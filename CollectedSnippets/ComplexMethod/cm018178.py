async def test_robot_with_update(
    hass: HomeAssistant, mock_account_with_litterrobot_4: MagicMock
) -> None:
    """Tests the update entity was set up."""
    robot: LitterRobot4 = mock_account_with_litterrobot_4.robots[0]
    robot.has_firmware_update = AsyncMock(return_value=True)
    robot.get_latest_firmware = AsyncMock(return_value=NEW_FIRMWARE)

    await setup_integration(hass, mock_account_with_litterrobot_4, UPDATE_DOMAIN)

    state = hass.states.get(ENTITY_ID)
    assert state
    assert state.state == STATE_ON
    assert state.attributes[ATTR_DEVICE_CLASS] == UpdateDeviceClass.FIRMWARE
    assert state.attributes[ATTR_INSTALLED_VERSION] == OLD_FIRMWARE
    assert state.attributes[ATTR_LATEST_VERSION] == NEW_FIRMWARE
    assert state.attributes[ATTR_RELEASE_URL] == RELEASE_URL

    robot.update_firmware = AsyncMock(return_value=False)

    with pytest.raises(HomeAssistantError, match="Unable to start firmware update"):
        await hass.services.async_call(
            UPDATE_DOMAIN,
            SERVICE_INSTALL,
            {ATTR_ENTITY_ID: ENTITY_ID},
            blocking=True,
        )
    await hass.async_block_till_done()
    assert robot.update_firmware.call_count == 1

    robot.update_firmware = AsyncMock(return_value=True)
    await hass.services.async_call(
        UPDATE_DOMAIN, SERVICE_INSTALL, {ATTR_ENTITY_ID: ENTITY_ID}, blocking=True
    )
    await hass.async_block_till_done()
    assert robot.update_firmware.call_count == 1