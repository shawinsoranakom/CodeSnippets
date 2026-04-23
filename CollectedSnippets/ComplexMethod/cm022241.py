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
        "sensor.test_monitored",
        16,
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] is None
    assert result["preview"] == "threshold"

    await client.send_json_auto_id(
        {
            "type": "threshold/start_preview",
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
    assert len(hass.states.async_all()) == 1