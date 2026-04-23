async def test_zeroconf(
    hass: HomeAssistant, mock_slide_api: AsyncMock, mock_setup_entry: AsyncMock
) -> None:
    """Test starting a flow from discovery."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_ZEROCONF}, data=MOCK_ZEROCONF_DATA
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "zeroconf_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "127.0.0.2"
    assert result["data"][CONF_HOST] == "127.0.0.2"
    assert not result["options"][CONF_INVERT_POSITION]
    assert result["result"].unique_id == "12:34:56:78:90:ab"