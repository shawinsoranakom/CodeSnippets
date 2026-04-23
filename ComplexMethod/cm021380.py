async def test_device_setup_update_authentication_error(hass: HomeAssistant) -> None:
    """Test we handle an authentication error in the update step."""
    device = get_device("Garage")
    mock_api = device.get_mock_api()
    mock_api.check_sensors.side_effect = blke.AuthorizationError()
    mock_api.auth.side_effect = (None, blke.AuthenticationError())

    with (
        patch.object(hass.config_entries, "async_forward_entry_setups") as mock_forward,
        patch.object(hass.config_entries.flow, "async_init") as mock_init,
    ):
        mock_setup = await device.setup_entry(hass, mock_api=mock_api)

    assert mock_setup.entry.state is ConfigEntryState.SETUP_RETRY
    assert mock_setup.api.auth.call_count == 2
    assert mock_setup.api.check_sensors.call_count == 1
    assert mock_forward.call_count == 0
    assert mock_init.call_count == 1
    assert mock_init.mock_calls[0][2]["context"]["source"] == "reauth"
    assert mock_init.mock_calls[0][2]["data"] == {
        "name": device.name,
        **device.get_entry_data(),
    }