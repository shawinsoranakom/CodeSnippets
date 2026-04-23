async def test_options_flow_preview(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    snapshot: SnapshotAssertion,
) -> None:
    """Test the options flow preview."""
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

    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            CONF_NAME: DEFAULT_NAME,
            CONF_INDOOR_TEMP: "sensor.indoor_temp",
            CONF_INDOOR_HUMIDITY: "sensor.indoor_humidity",
            CONF_OUTDOOR_TEMP: "sensor.outdoor_temp",
            CONF_CALIBRATION_FACTOR: 2.0,
        },
        title="Test Sensor",
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None
    assert result["preview"] == "mold_indicator"

    await client.send_json_auto_id(
        {
            "type": "mold_indicator/start_preview",
            "flow_id": result["flow_id"],
            "flow_type": "options_flow",
            "user_input": {
                CONF_NAME: DEFAULT_NAME,
                CONF_INDOOR_TEMP: "sensor.indoor_temp",
                CONF_INDOOR_HUMIDITY: "sensor.indoor_humidity",
                CONF_OUTDOOR_TEMP: "sensor.outdoor_temp",
                CONF_CALIBRATION_FACTOR: 2.0,
            },
        }
    )
    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] is None

    msg = await client.receive_json()
    assert msg["event"] == snapshot
    assert len(hass.states.async_all()) == 4