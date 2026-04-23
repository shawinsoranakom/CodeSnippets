async def test_sensor_created_after_websocket_update_when_initial_fetch_fails(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_client: MagicMock,
) -> None:
    """Test websocket updates refine placeholder sensors after a transient startup error."""
    mock_client.get_door_lock_rule = AsyncMock(
        side_effect=ApiConnectionError("Connection failed")
    )

    with patch("homeassistant.components.unifi_access.PLATFORMS", [Platform.SENSOR]):
        await setup_integration(hass, mock_config_entry)

    assert hass.states.get(FRONT_DOOR_LOCK_RULE_ENTITY).state == "unknown"
    assert hass.states.get(FRONT_DOOR_LOCK_RULE_END_TIME_ENTITY).state == "unknown"
    assert hass.states.get(BACK_DOOR_LOCK_RULE_ENTITY).state == "unknown"
    assert hass.states.get(BACK_DOOR_LOCK_RULE_END_TIME_ENTITY).state == "unknown"

    handlers = _get_ws_handlers(mock_client)
    update_msg = LocationUpdateV2(
        event="access.data.device.location_update_v2",
        data=LocationUpdateData(
            id="door-001",
            location_type="DOOR",
            state=LocationUpdateState(
                remain_lock=WsDoorLockRuleStatus(
                    type=DoorLockRuleType.KEEP_LOCK,
                    until=1700000000,
                )
            ),
        ),
    )
    await handlers["access.data.device.location_update_v2"](update_msg)
    await hass.async_block_till_done()

    assert hass.states.get(FRONT_DOOR_LOCK_RULE_ENTITY).state == "keep_lock"
    assert hass.states.get(FRONT_DOOR_LOCK_RULE_END_TIME_ENTITY).state == (
        datetime.fromtimestamp(1700000000, tz=UTC).isoformat()
    )
    assert hass.states.get(BACK_DOOR_LOCK_RULE_ENTITY).state == "unknown"
    assert hass.states.get(BACK_DOOR_LOCK_RULE_END_TIME_ENTITY).state == "unknown"