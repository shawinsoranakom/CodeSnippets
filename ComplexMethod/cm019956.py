async def test_zeroconf_confirm_create_entry(
    hass: HomeAssistant, mock_brother_client: AsyncMock
) -> None:
    """Test zeroconf confirmation and create config entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_ZEROCONF},
        data=ZeroconfServiceInfo(
            ip_address=ip_address("127.0.0.1"),
            ip_addresses=[ip_address("127.0.0.1")],
            hostname="example.local.",
            name="Brother Printer",
            port=None,
            properties={},
            type="mock_type",
        ),
    )

    assert result["step_id"] == "zeroconf_confirm"
    assert result["description_placeholders"]["model"] == "HL-L2340DW"
    assert result["description_placeholders"]["serial_number"] == "0123456789"
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_TYPE: "laser",
            SECTION_ADVANCED_SETTINGS: {CONF_PORT: 161, CONF_COMMUNITY: "public"},
        },
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "HL-L2340DW 0123456789"
    assert result["data"][CONF_HOST] == "127.0.0.1"
    assert result["data"][CONF_TYPE] == "laser"
    assert result["data"][SECTION_ADVANCED_SETTINGS][CONF_PORT] == 161
    assert result["data"][SECTION_ADVANCED_SETTINGS][CONF_COMMUNITY] == "public"
    assert result["result"].unique_id == "0123456789"