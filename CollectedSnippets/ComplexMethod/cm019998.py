async def test_flow_manual_configuration(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test that config flow works with manual configuration after no discovered bridges."""
    logging.getLogger("homeassistant.components.deconz").setLevel(logging.DEBUG)
    aioclient_mock.get(
        pydeconz.utils.URL_DISCOVER,
        json=[],
        headers={"content-type": CONTENT_TYPE_JSON},
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual_input"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "1.2.3.4", CONF_PORT: 80},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "link"

    aioclient_mock.post(
        "http://1.2.3.4:80/api",
        json=[{"success": {"username": API_KEY}}],
        headers={"content-type": CONTENT_TYPE_JSON},
    )

    aioclient_mock.get(
        f"http://1.2.3.4:80/api/{API_KEY}/config",
        json={"bridgeid": BRIDGE_ID},
        headers={"content-type": CONTENT_TYPE_JSON},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == BRIDGE_ID
    assert result["data"] == {
        CONF_HOST: "1.2.3.4",
        CONF_PORT: 80,
        CONF_API_KEY: API_KEY,
    }