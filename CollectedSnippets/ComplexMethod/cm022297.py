async def test_dhcp_discovery_new_device(
    hass: HomeAssistant,
    mock_duco_client: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test DHCP discovery of a new device shows confirmation form and creates entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DHCP_DISCOVERY,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovery_confirm"
    assert result["description_placeholders"] == {"name": "SILENT_CONNECT"}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "SILENT_CONNECT"
    assert result["data"] == USER_INPUT
    assert result["result"].unique_id == TEST_MAC