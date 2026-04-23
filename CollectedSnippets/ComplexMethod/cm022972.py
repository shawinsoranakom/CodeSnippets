async def test_full_zeroconf_flow_implementation(hass: HomeAssistant) -> None:
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

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1

    assert (
        flows[0].get("context", {}).get("configuration_url") == "http://192.168.1.123"
    )
    assert result.get("description_placeholders") == {CONF_NAME: "WLED RGB Light"}
    assert result.get("step_id") == "zeroconf_confirm"
    assert result.get("type") is FlowResultType.FORM

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result2.get("title") == "WLED RGB Light"
    assert result2.get("type") is FlowResultType.CREATE_ENTRY

    assert "data" in result2
    assert result2["data"][CONF_HOST] == "192.168.1.123"
    assert "result" in result2
    assert result2["result"].unique_id == "aabbccddeeff"