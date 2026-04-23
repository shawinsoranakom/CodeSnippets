async def test_dhcp_discovery_errors(
    hass: HomeAssistant,
    mock_pyvlx: AsyncMock,
    exception: Exception,
    error: str,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test we can setup from dhcp discovery."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_DHCP},
        data=DHCP_DISCOVERY,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovery_confirm"

    mock_pyvlx.connect.side_effect = exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "NotAStrongPassword"},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "discovery_confirm"
    assert result["errors"] == {"base": error}

    mock_pyvlx.connect.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_PASSWORD: "NotAStrongPassword"},
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "VELUX_KLF_ABCD"
    assert result["data"] == {
        CONF_HOST: "127.0.0.1",
        CONF_MAC: "64:61:84:00:ab:cd",
        CONF_NAME: "VELUX_KLF_ABCD",
        CONF_PASSWORD: "NotAStrongPassword",
    }