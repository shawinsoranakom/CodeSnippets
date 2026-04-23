async def test_diagnostics(
    hass: HomeAssistant,
    device_registry: dr.DeviceRegistry,
    hass_client: ClientSessionGenerator,
    mock_fully_kiosk: MagicMock,
    init_integration: MockConfigEntry,
) -> None:
    """Test Fully Kiosk diagnostics."""
    device = device_registry.async_get_device(identifiers={(DOMAIN, "abcdef-123456")})

    diagnostics = await get_diagnostics_for_device(
        hass, hass_client, init_integration, device
    )

    assert diagnostics
    for key in DEVICE_INFO_TO_REDACT:
        if hasattr(diagnostics, key):
            assert diagnostics[key] == REDACTED
    for key in SETTINGS_TO_REDACT:
        if hasattr(diagnostics["settings"], key):
            assert (
                diagnostics["settings"][key] == REDACTED
                or diagnostics["settings"][key] == ""
            )