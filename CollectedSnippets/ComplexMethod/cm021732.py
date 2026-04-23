async def test_dhcp_flow(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test the full DHCP config flow."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            ip="192.168.0.123", hostname="kommspot", macaddress="a4e57caabbcc"
        ),
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "dhcp_confirm"

    result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "PoolDose TEST123456789"
    assert result["data"][CONF_HOST] == "192.168.0.123"
    assert result["data"][CONF_MAC] == "a4e57caabbcc"
    assert result["result"].unique_id == "TEST123456789"