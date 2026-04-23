async def test_full_zeroconf_flow_implementationn(
    hass: HomeAssistant,
    mock_pure_energie_config_flow: MagicMock,
    mock_setup_entry: None,
) -> None:
    """Test the full manual user flow from start to finish."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("192.168.1.123"),
            ip_addresses=[ip_address("192.168.1.123")],
            hostname="example.local.",
            name="mock_name",
            port=None,
            properties={CONF_MAC: "aabbccddeeff"},
            type="mock_type",
        ),
    )

    assert result.get("description_placeholders") == {
        "model": "SBWF3102",
        CONF_NAME: "Pure Energie Meter",
    }
    assert result.get("step_id") == "zeroconf_confirm"
    assert result.get("type") is FlowResultType.FORM

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result2.get("title") == "Pure Energie Meter"
    assert result2.get("type") is FlowResultType.CREATE_ENTRY

    assert "data" in result2
    assert result2["data"][CONF_HOST] == "192.168.1.123"
    assert "result" in result2
    assert result2["result"].unique_id == "aabbccddeeff"