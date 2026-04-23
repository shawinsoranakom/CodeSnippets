async def test_options_flow_preview(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    snapshot: SnapshotAssertion,
) -> None:
    """Test the options flow preview."""
    client = await hass_ws_client(hass)

    # add state for the tests
    hass.states.async_set("sensor.test_monitored", "16")

    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            CONF_NAME: DEFAULT_NAME,
            CONF_ENTITY_ID: "sensor.test_monitored",
            CONF_STATE_CHARACTERISTIC: STAT_VALUE_MAX,
            CONF_SAMPLES_MAX_BUFFER_SIZE: 20.0,
            CONF_MAX_AGE: {"hours": 8, "minutes": 0, "seconds": 0},
            CONF_KEEP_LAST_SAMPLE: False,
            CONF_PERCENTILE: 50.0,
            CONF_PRECISION: 2.0,
        },
        title=DEFAULT_NAME,
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None
    assert result["preview"] == "statistics"

    await client.send_json_auto_id(
        {
            "type": "statistics/start_preview",
            "flow_id": result["flow_id"],
            "flow_type": "options_flow",
            "user_input": {
                CONF_SAMPLES_MAX_BUFFER_SIZE: 20.0,
                CONF_MAX_AGE: {"hours": 8, "minutes": 0, "seconds": 0},
                CONF_KEEP_LAST_SAMPLE: False,
                CONF_PERCENTILE: 50.0,
                CONF_PRECISION: 2.0,
            },
        }
    )

    msg = await client.receive_json()
    assert msg["success"]
    assert msg["result"] is None

    msg = await client.receive_json()
    assert msg["event"] == snapshot
    assert len(hass.states.async_all()) == 2

    # add state for the tests
    hass.states.async_set("sensor.test_monitored", "20")
    await hass.async_block_till_done()

    msg = await client.receive_json()
    assert msg["event"] == snapshot(name="updated")