async def test_flow_works(hass: HomeAssistant) -> None:
    """Test config flow ."""
    disc_bridge = get_discovered_bridge(supports_v2=True)

    with patch(
        "homeassistant.components.hue.config_flow.discover_nupnp",
        return_value=[disc_bridge],
    ):
        result = await hass.config_entries.flow.async_init(
            const.DOMAIN, context={"source": config_entries.SOURCE_USER}
        )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"id": disc_bridge.id}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "link"

    flow = next(
        flow
        for flow in hass.config_entries.flow.async_progress()
        if flow["flow_id"] == result["flow_id"]
    )
    assert flow["context"]["unique_id"] == "aabbccddeeff"

    with patch.object(config_flow, "create_app_key", return_value="123456789"):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], user_input={}
        )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Hue Bridge aabbccddeeff"
    assert result["data"] == {
        "host": "1.2.3.4",
        "api_key": "123456789",
        "api_version": 2,
    }