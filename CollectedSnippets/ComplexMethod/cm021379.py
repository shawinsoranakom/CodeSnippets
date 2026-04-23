async def test_device_setup(hass: HomeAssistant) -> None:
    """Test a successful setup."""
    device = get_device("Office")

    with (
        patch.object(hass.config_entries, "async_forward_entry_setups") as mock_forward,
        patch.object(hass.config_entries.flow, "async_init") as mock_init,
    ):
        mock_setup = await device.setup_entry(hass)

    assert mock_setup.entry.state is ConfigEntryState.LOADED
    assert mock_setup.api.auth.call_count == 1
    assert mock_setup.api.get_fwversion.call_count == 1
    assert mock_setup.factory.call_count == 1

    forward_entries = set(mock_forward.mock_calls[0][1][1])
    domains = get_domains(mock_setup.api.type)
    assert mock_forward.call_count == 1
    assert forward_entries == domains
    assert mock_init.call_count == 0