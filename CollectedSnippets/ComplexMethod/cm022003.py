async def test_dhcp_discovery_if_panel_setup_config_flow(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
    mock_panel: AsyncMock,
    serial_number: str,
    panel_model: PanelModel,
    config_flow_data: dict[str, Any],
) -> None:
    """Test DHCP discovery doesn't fail if a different panel was set up via config flow."""
    await setup_integration(hass, mock_config_entry)

    # change out the serial number so we can test discovery for a different panel
    mock_panel.serial_number = "789101112"
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DhcpServiceInfo(
            hostname="test",
            ip="4.5.6.7",
            macaddress="34ea34b43b5a",
        ),
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "auth"
    assert result["errors"] == {}
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        config_flow_data,
    )

    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"Bosch {panel_model.name}"
    assert result["data"] == {
        CONF_HOST: "4.5.6.7",
        CONF_MAC: "34:ea:34:b4:3b:5a",
        CONF_PORT: 7700,
        CONF_MODEL: panel_model.name,
        **config_flow_data,
    }
    assert mock_config_entry.unique_id == serial_number
    assert result["result"].unique_id == "789101112"