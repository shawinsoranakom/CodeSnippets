async def test_buttons(
    hass: HomeAssistant,
    mock_peblar: MagicMock,
    mock_config_entry: MockConfigEntry,
    entity_id: str,
    method: str,
) -> None:
    """Test the Peblar EV charger buttons."""
    mocked_method = getattr(mock_peblar, method)

    # Test normal happy path button press
    await hass.services.async_call(
        BUTTON_DOMAIN,
        SERVICE_PRESS,
        {ATTR_ENTITY_ID: entity_id},
        blocking=True,
    )

    assert len(mocked_method.mock_calls) == 1
    mocked_method.assert_called_with()

    # Test connection error handling
    mocked_method.side_effect = PeblarConnectionError("Could not connect")
    with pytest.raises(
        HomeAssistantError,
        match=(
            r"An error occurred while communicating "
            r"with the Peblar EV charger: Could not connect"
        ),
    ) as excinfo:
        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

    assert excinfo.value.translation_domain == DOMAIN
    assert excinfo.value.translation_key == "communication_error"
    assert excinfo.value.translation_placeholders == {"error": "Could not connect"}

    # Test unknown error handling
    mocked_method.side_effect = PeblarError("Unknown error")
    with pytest.raises(
        HomeAssistantError,
        match=(
            r"An unknown error occurred while communicating "
            r"with the Peblar EV charger: Unknown error"
        ),
    ) as excinfo:
        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

    assert excinfo.value.translation_domain == DOMAIN
    assert excinfo.value.translation_key == "unknown_error"
    assert excinfo.value.translation_placeholders == {"error": "Unknown error"}

    # Test authentication error handling
    mocked_method.side_effect = PeblarAuthenticationError("Authentication error")
    mock_peblar.login.side_effect = PeblarAuthenticationError("Authentication error")
    with pytest.raises(
        HomeAssistantError,
        match=(
            r"An authentication failure occurred while communicating "
            r"with the Peblar EV charger"
        ),
    ) as excinfo:
        await hass.services.async_call(
            BUTTON_DOMAIN,
            SERVICE_PRESS,
            {ATTR_ENTITY_ID: entity_id},
            blocking=True,
        )

    assert excinfo.value.translation_domain == DOMAIN
    assert excinfo.value.translation_key == "authentication_error"
    assert not excinfo.value.translation_placeholders

    # Ensure the device is reloaded on authentication error and triggers
    # a reauthentication flow.
    await hass.async_block_till_done()
    assert mock_config_entry.state is ConfigEntryState.SETUP_ERROR

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    flow = flows[0]
    assert flow["step_id"] == "reauth_confirm"
    assert flow["handler"] == DOMAIN

    assert "context" in flow
    assert flow["context"].get("source") == SOURCE_REAUTH
    assert flow["context"].get("entry_id") == mock_config_entry.entry_id