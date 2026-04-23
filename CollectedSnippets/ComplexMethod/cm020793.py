async def test_config_flow_preview_success(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    user_input: str,
    snapshot: SnapshotAssertion,
) -> None:
    """Test the config flow preview."""
    client = await hass_ws_client(hass)

    # add state for the tests
    hass.states.async_set(
        "sensor.indoor_temp",
        23,
        {CONF_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
    )
    hass.states.async_set(
        "sensor.indoor_humidity",
        50,
        {CONF_UNIT_OF_MEASUREMENT: "%"},
    )
    hass.states.async_set(
        "sensor.outdoor_temp",
        16,
        {CONF_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] is None
    assert result["preview"] == "mold_indicator"

    await client.send_json_auto_id(
        {
            "type": "mold_indicator/start_preview",
            "flow_id": result["flow_id"],
            "flow_type": "config_flow",
            "user_input": user_input,
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] is None

    msg = await client.receive_json()
    assert msg["event"] == snapshot
    assert len(hass.states.async_all()) == 3