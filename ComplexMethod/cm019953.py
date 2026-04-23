async def test_create_entry(
    hass: HomeAssistant, host: str, mock_brother_client: AsyncMock
) -> None:
    """Test that the user step works with printer hostname/IPv4/IPv6."""
    config = CONFIG.copy()
    config[CONF_HOST] = host

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        flow_id=result["flow_id"],
        user_input=config,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "HL-L2340DW 0123456789"
    assert result["data"][CONF_HOST] == host
    assert result["data"][CONF_TYPE] == "laser"
    assert result["data"][SECTION_ADVANCED_SETTINGS][CONF_PORT] == 161
    assert result["data"][SECTION_ADVANCED_SETTINGS][CONF_COMMUNITY] == "public"
    assert result["result"].unique_id == "0123456789"