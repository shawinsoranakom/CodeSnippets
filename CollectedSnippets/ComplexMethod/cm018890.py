async def test_auth_failed_error(
    hass: HomeAssistant,
    mock_nice_go: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that if an auth failed error occurs, the integration attempts a token refresh and a retry before throwing an error."""

    await setup_integration(hass, mock_config_entry, [Platform.COVER])

    def _open_side_effect(*args, **kwargs):
        if mock_nice_go.open_barrier.call_count <= 3:
            raise AuthFailedError
        if mock_nice_go.open_barrier.call_count == 5:
            raise AuthFailedError
        if mock_nice_go.open_barrier.call_count == 6:
            raise ApiError

    def _close_side_effect(*args, **kwargs):
        if mock_nice_go.close_barrier.call_count <= 3:
            raise AuthFailedError
        if mock_nice_go.close_barrier.call_count == 4:
            raise ApiError

    mock_nice_go.open_barrier.side_effect = _open_side_effect
    mock_nice_go.close_barrier.side_effect = _close_side_effect

    with pytest.raises(HomeAssistantError, match="Error opening the barrier"):
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_OPEN_COVER,
            {ATTR_ENTITY_ID: "cover.test_garage_1"},
            blocking=True,
        )

    assert mock_nice_go.authenticate.call_count == 1
    assert mock_nice_go.open_barrier.call_count == 2

    with pytest.raises(HomeAssistantError, match="Error closing the barrier"):
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_CLOSE_COVER,
            {ATTR_ENTITY_ID: "cover.test_garage_2"},
            blocking=True,
        )

    assert mock_nice_go.authenticate.call_count == 2
    assert mock_nice_go.close_barrier.call_count == 2

    # Try again, but this time the auth failed error should not be raised

    await hass.services.async_call(
        COVER_DOMAIN,
        SERVICE_OPEN_COVER,
        {ATTR_ENTITY_ID: "cover.test_garage_1"},
        blocking=True,
    )

    assert mock_nice_go.authenticate.call_count == 3
    assert mock_nice_go.open_barrier.call_count == 4

    # One more time but with an ApiError instead of AuthFailed

    with pytest.raises(HomeAssistantError, match="Error opening the barrier"):
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_OPEN_COVER,
            {ATTR_ENTITY_ID: "cover.test_garage_1"},
            blocking=True,
        )

    with pytest.raises(HomeAssistantError, match="Error closing the barrier"):
        await hass.services.async_call(
            COVER_DOMAIN,
            SERVICE_CLOSE_COVER,
            {ATTR_ENTITY_ID: "cover.test_garage_2"},
            blocking=True,
        )

    assert mock_nice_go.authenticate.call_count == 5
    assert mock_nice_go.open_barrier.call_count == 6
    assert mock_nice_go.close_barrier.call_count == 4