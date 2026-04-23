async def test_discovery_flow_during_onboarding_disabled_api(
    hass: HomeAssistant,
    mock_homewizardenergy: MagicMock,
    mock_setup_entry: AsyncMock,
    mock_onboarding: MagicMock,
    snapshot: SnapshotAssertion,
) -> None:
    """Test discovery setup flow during onboarding with a disabled API."""
    mock_homewizardenergy.device.side_effect = DisabledError

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            port=80,
            hostname="p1meter-ddeeff.local.",
            type="mock_type",
            name="mock_name",
            properties={
                "api_enabled": "0",
                "path": "/api/v1",
                "product_name": "P1 meter",
                "product_type": "HWE-P1",
                "serial": "5c2fafabcdef",
            },
        ),
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovery_confirm"
    assert result["errors"] == {"base": "api_not_enabled"}

    # We are onboarded, user enabled API again and picks up from discovery/config flow
    mock_homewizardenergy.device.side_effect = None
    mock_onboarding.return_value = True

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"ip_address": "127.0.0.1"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result == snapshot

    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_onboarding.mock_calls) == 1