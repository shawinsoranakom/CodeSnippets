async def test_zeroconf(hass: HomeAssistant) -> None:
    """Test starting a flow from zeroconf."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": config_entries.SOURCE_ZEROCONF},
        data=MOCK_ZEROCONF_DATA,
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "confirm"

    # entry was added
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input="whatever"
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Living Room (82GXARRS)"
    assert result["data"][CONF_HOST] == "127.0.0.1"
    assert result["data"][CONF_MAC] == "aa:bb:aa:aa:aa:aa"
    assert result["data"][CONF_MANUFACTURER] == "Samsung"
    assert result["data"][CONF_MODEL] == "82GXARRS"
    assert result["data"][CONF_PORT] == 8002
    assert result["result"].unique_id == "be9554b9-c9fb-41f4-8920-22da015376a4"