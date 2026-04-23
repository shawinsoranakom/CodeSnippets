async def test_cover_entity(
    hass: HomeAssistant,
    mock_client: APIClient,
    mock_esphome_device: MockESPHomeDeviceType,
) -> None:
    """Test a generic cover entity."""
    entity_info = [
        CoverInfo(
            object_id="mycover",
            key=1,
            name="my cover",
            supports_position=True,
            supports_tilt=True,
            supports_stop=True,
        )
    ]
    states = [
        ESPHomeCoverState(
            key=1,
            position=0.5,
            tilt=0.5,
            current_operation=CoverOperation.IS_OPENING,
        )
    ]
    user_service = []
    mock_device = await mock_esphome_device(
        mock_client=mock_client,
        entity_info=entity_info,
        user_service=user_service,
        states=states,
    )
    state = hass.states.get("cover.test_my_cover")
    assert state is not None
    assert state.state == CoverState.OPENING
    assert state.attributes[ATTR_CURRENT_POSITION] == 50
    assert state.attributes[ATTR_CURRENT_TILT_POSITION] == 50

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER,
        {ATTR_ENTITY_ID: "cover.test_my_cover"},
        blocking=True,
    )
    mock_client.cover_command.assert_has_calls([call(key=1, position=0.0, device_id=0)])
    mock_client.cover_command.reset_mock()

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: "cover.test_my_cover"},
        blocking=True,
    )
    mock_client.cover_command.assert_has_calls([call(key=1, position=1.0, device_id=0)])
    mock_client.cover_command.reset_mock()

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_POSITION,
        {ATTR_ENTITY_ID: "cover.test_my_cover", ATTR_POSITION: 50},
        blocking=True,
    )
    mock_client.cover_command.assert_has_calls([call(key=1, position=0.5, device_id=0)])
    mock_client.cover_command.reset_mock()

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_STOP_COVER,
        {ATTR_ENTITY_ID: "cover.test_my_cover"},
        blocking=True,
    )
    mock_client.cover_command.assert_has_calls([call(key=1, stop=True, device_id=0)])
    mock_client.cover_command.reset_mock()

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER_TILT,
        {ATTR_ENTITY_ID: "cover.test_my_cover"},
        blocking=True,
    )
    mock_client.cover_command.assert_has_calls([call(key=1, tilt=1.0, device_id=0)])
    mock_client.cover_command.reset_mock()

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_CLOSE_COVER_TILT,
        {ATTR_ENTITY_ID: "cover.test_my_cover"},
        blocking=True,
    )
    mock_client.cover_command.assert_has_calls([call(key=1, tilt=0.0, device_id=0)])
    mock_client.cover_command.reset_mock()

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_TILT_POSITION,
        {ATTR_ENTITY_ID: "cover.test_my_cover", ATTR_TILT_POSITION: 50},
        blocking=True,
    )
    mock_client.cover_command.assert_has_calls([call(key=1, tilt=0.5, device_id=0)])
    mock_client.cover_command.reset_mock()

    mock_device.set_state(
        ESPHomeCoverState(key=1, position=0.0, current_operation=CoverOperation.IDLE)
    )
    await hass.async_block_till_done()
    state = hass.states.get("cover.test_my_cover")
    assert state is not None
    assert state.state == CoverState.CLOSED

    mock_device.set_state(
        ESPHomeCoverState(
            key=1, position=0.5, current_operation=CoverOperation.IS_CLOSING
        )
    )
    await hass.async_block_till_done()
    state = hass.states.get("cover.test_my_cover")
    assert state is not None
    assert state.state == CoverState.CLOSING

    mock_device.set_state(
        ESPHomeCoverState(key=1, position=1.0, current_operation=CoverOperation.IDLE)
    )
    await hass.async_block_till_done()
    state = hass.states.get("cover.test_my_cover")
    assert state is not None
    assert state.state == CoverState.OPEN