async def test_flow_ssdp(hass: HomeAssistant) -> None:
    """Test working ssdp flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_SSDP},
        data=SSDP_DATA,
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    assert result["description_placeholders"] == {
        CONF_NAME: FRIENDLY_NAME,
        CONF_HOST: HOST,
    }
    flow = _flow_next(hass, result["flow_id"])
    assert flow["context"]["unique_id"] == UDN

    with _patch_setup():
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )
        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["title"] == FRIENDLY_NAME
        assert result["data"] == CONF_DATA