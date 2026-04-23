async def test_dhcp_flow_wih_auth(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_incomfort: MagicMock
) -> None:
    """Test dhcp flow for with authentication."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_DHCP}, data=DHCP_SERVICE_INFO
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "dhcp_confirm"

    # Try again, but now with the correct host, but still with an auth error
    with patch.object(
        mock_incomfort(),
        "heaters",
        side_effect=InvalidGateway,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], {CONF_HOST: "192.168.1.12"}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "dhcp_auth"
    assert result["errors"] == {"base": "auth_error"}

    # Submit the form with added credentials
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], MOCK_CONFIG_DHCP
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Intergas InComfort/Intouch Lan2RF gateway"
    assert result["data"] == MOCK_CONFIG
    assert len(mock_setup_entry.mock_calls) == 1