async def test_flow_discovered_bridges(
    hass: HomeAssistant, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test that config flow works for discovered bridges."""
    logging.getLogger("homeassistant.components.deconz").setLevel(logging.DEBUG)
    aioclient_mock.get(
        pydeconz.utils.URL_DISCOVER,
        json=[
            {"id": BRIDGE_ID, "internalipaddress": "1.2.3.4", "internalport": 80},
            {"id": "1234E567890A", "internalipaddress": "5.6.7.8", "internalport": 80},
        ],
        headers={"content-type": CONTENT_TYPE_JSON},
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "1.2.3.4"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "link"

    aioclient_mock.post(
        "http://1.2.3.4:80/api",
        json=[{"success": {"username": API_KEY}}],
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