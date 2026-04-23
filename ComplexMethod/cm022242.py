async def test_options_flow_preview(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    snapshot: SnapshotAssertion,
) -> None:
    """Test the options flow preview."""
    client = await hass_ws_client(hass)

    # add state for the tests
    hass.states.async_set(
        "sensor.test_monitored",
        16,
        {ATTR_UNIT_OF_MEASUREMENT: UnitOfTemperature.CELSIUS},
    )

    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "entity_id": "sensor.test_monitored",
            "hysteresis": 0.0,
            "lower": 20.0,
            "name": "Test Sensor",
            "upper": None,
        },
        title="Test Sensor",
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None
    assert result["preview"] == "threshold"

    await client.send_json_auto_id(
        {
            "type": "threshold/start_preview",
            "flow_id": result["flow_id"],
            "flow_type": "options_flow",
            "user_input": {
                "name": "Test Sensor",
                "entity_id": "sensor.test_monitored",
                "hysteresis": 0.0,
                "lower": 20.0,
            },
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] is None

    msg = await client.receive_json()
    assert msg["event"] == snapshot
    assert len(hass.states.async_all()) == 2