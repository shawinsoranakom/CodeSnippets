async def test_dual_shutter_set_cover_position_inversion(
    hass: HomeAssistant, mock_dual_roller_shutter: AsyncMock
) -> None:
    """HA position is inverted for device's Position."""

    entity_id = "cover.test_dual_roller_shutter"
    # Call with position 30 (=70% for device)
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_POSITION,
        {"entity_id": entity_id, ATTR_POSITION: 30},
        blocking=True,
    )

    # Expect device Position 70%
    args, kwargs = mock_dual_roller_shutter.set_position.await_args
    position_obj = args[0]
    assert position_obj.position_percent == 70
    assert kwargs.get("wait_for_completion") is False
    assert kwargs.get("curtain") == "dual"

    entity_id = "cover.test_dual_roller_shutter_upper_shutter"
    # Call with position 30 (=70% for device)
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_POSITION,
        {"entity_id": entity_id, ATTR_POSITION: 30},
        blocking=True,
    )

    # Expect device Position 70%
    args, kwargs = mock_dual_roller_shutter.set_position.await_args
    position_obj = args[0]
    assert position_obj.position_percent == 70
    assert kwargs.get("wait_for_completion") is False
    assert kwargs.get("curtain") == "upper"

    entity_id = "cover.test_dual_roller_shutter_lower_shutter"
    # Call with position 30 (=70% for device)
    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_SET_COVER_POSITION,
        {"entity_id": entity_id, ATTR_POSITION: 30},
        blocking=True,
    )

    # Expect device Position 70%
    args, kwargs = mock_dual_roller_shutter.set_position.await_args
    position_obj = args[0]
    assert position_obj.position_percent == 70
    assert kwargs.get("wait_for_completion") is False
    assert kwargs.get("curtain") == "lower"