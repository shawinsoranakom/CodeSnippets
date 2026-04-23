async def test_full_ssdp_flow_implementation(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test the full SSDP flow from start to finish."""
    mock_connection(aioclient_mock)

    discovery_info = dataclasses.replace(MOCK_SSDP_DISCOVERY_INFO)
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_SSDP}, data=discovery_info
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "ssdp_confirm"
    assert result["description_placeholders"] == {CONF_NAME: HOST}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == HOST

    assert result["data"]
    assert result["data"][CONF_HOST] == HOST
    assert result["data"][CONF_RECEIVER_ID] == RECEIVER_ID