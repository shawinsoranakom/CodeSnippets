async def test_zeroconf_during_onboarding(
    hass: HomeAssistant,
    mock_elgato: MagicMock,
    mock_setup_entry: AsyncMock,
    mock_onboarding: MagicMock,
) -> None:
    """Test the zeroconf creates an entry during onboarding."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            hostname="example.local.",
            name="mock_name",
            port=9123,
            properties={"id": "AA:BB:CC:DD:EE:FF"},
            type="mock_type",
        ),
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY

    config_entry = result["result"]
    assert config_entry.unique_id == "CN11A1A00001"
    assert config_entry.data == {
        CONF_HOST: "127.0.0.1",
        CONF_MAC: "AA:BB:CC:DD:EE:FF",
    }
    assert not config_entry.options

    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_elgato.info.mock_calls) == 1
    assert len(mock_onboarding.mock_calls) == 1