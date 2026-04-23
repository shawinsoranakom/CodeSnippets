async def test_config_flow_from_dhcp_ip_update(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_hub_refresh: AsyncMock,
) -> None:
    """Test we can use DHCP discovery to update IP in a config entry."""
    info = DhcpServiceInfo(
        ip="1.2.3.4", hostname="webcontrol", macaddress="001122334455"
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=info
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    with patch(
        "wmspro.webcontrol.WebControlPro.ping",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_HOST: "1.2.3.4",
            },
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "1.2.3.4"
    assert result["data"] == {
        CONF_HOST: "1.2.3.4",
    }
    assert len(mock_setup_entry.mock_calls) == 1
    assert hass.config_entries.async_entries(DOMAIN)[0].unique_id == "00:11:22:33:44:55"

    info = DhcpServiceInfo(
        ip="5.6.7.8", hostname="webcontrol", macaddress="001122334455"
    )
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=info
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert hass.config_entries.async_entries(DOMAIN)[0].unique_id == "00:11:22:33:44:55"
    assert hass.config_entries.async_entries(DOMAIN)[0].data[CONF_HOST] == "5.6.7.8"