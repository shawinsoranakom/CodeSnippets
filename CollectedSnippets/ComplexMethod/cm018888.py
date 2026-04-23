async def test_auth_failed_error(
    hass: HomeAssistant,
    mock_nice_go: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that if an auth failed error occurs, the integration attempts a token refresh and a retry before throwing an error."""

    await setup_integration(hass, mock_config_entry, [Platform.SWITCH])

    def _on_side_effect(*args, **kwargs):
        if mock_nice_go.vacation_mode_on.call_count <= 3:
            raise AuthFailedError
        if mock_nice_go.vacation_mode_on.call_count == 5:
            raise AuthFailedError
        if mock_nice_go.vacation_mode_on.call_count == 6:
            raise ApiError

    def _off_side_effect(*args, **kwargs):
        if mock_nice_go.vacation_mode_off.call_count <= 3:
            raise AuthFailedError
        if mock_nice_go.vacation_mode_off.call_count == 4:
            raise ApiError

    mock_nice_go.vacation_mode_on.side_effect = _on_side_effect
    mock_nice_go.vacation_mode_off.side_effect = _off_side_effect

    with pytest.raises(HomeAssistantError, match="Error while turning on the switch"):
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.test_garage_1_vacation_mode"},
            blocking=True,
        )

    assert mock_nice_go.authenticate.call_count == 1
    assert mock_nice_go.vacation_mode_on.call_count == 2

    with pytest.raises(HomeAssistantError, match="Error while turning off the switch"):
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "switch.test_garage_2_vacation_mode"},
            blocking=True,
        )

    assert mock_nice_go.authenticate.call_count == 2
    assert mock_nice_go.vacation_mode_off.call_count == 2

    # Try again, but this time the auth failed error should not be raised

    await hass.services.async_call(
        SWITCH_DOMAIN,
        SERVICE_TURN_ON,
        {ATTR_ENTITY_ID: "switch.test_garage_1_vacation_mode"},
        blocking=True,
    )

    assert mock_nice_go.authenticate.call_count == 3
    assert mock_nice_go.vacation_mode_on.call_count == 4

    # One more time but with an ApiError instead of AuthFailed

    with pytest.raises(HomeAssistantError, match="Error while turning on the switch"):
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_ON,
            {ATTR_ENTITY_ID: "switch.test_garage_1_vacation_mode"},
            blocking=True,
        )

    with pytest.raises(HomeAssistantError, match="Error while turning off the switch"):
        await hass.services.async_call(
            SWITCH_DOMAIN,
            SERVICE_TURN_OFF,
            {ATTR_ENTITY_ID: "switch.test_garage_2_vacation_mode"},
            blocking=True,
        )

    assert mock_nice_go.authenticate.call_count == 5
    assert mock_nice_go.vacation_mode_on.call_count == 6
    assert mock_nice_go.vacation_mode_off.call_count == 4