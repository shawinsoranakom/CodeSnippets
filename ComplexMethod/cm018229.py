async def test_zeroconf_during_onboarding(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_onboarding: MagicMock,
) -> None:
    """Test we create a config entry when discovered during onboarding."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.123"),
            ip_addresses=[ip_address("192.168.1.123")],
            hostname="example.local.",
            name="mock_name",
            port=None,
            properties={CONF_MAC: "AA:AA:AA:AA:AA:BB"},
            type="mock_type",
        ),
    )

    assert result.get("title") == "TechnoVE Station"
    assert result.get("type") is FlowResultType.CREATE_ENTRY

    assert result.get("data") == {CONF_HOST: "192.168.1.123"}
    assert "result" in result
    assert result["result"].unique_id == "AA:AA:AA:AA:AA:BB"

    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_onboarding.mock_calls) == 1