async def test_config_flow_preview_success(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test the config flow preview."""
    client = await hass_ws_client(hass)

    # add state for the tests
    await hass.config.async_set_time_zone("UTC")
    utcnow = dt_util.utcnow()
    start_time = utcnow.replace(hour=0, minute=0, second=0, microsecond=0)
    t1 = start_time.replace(hour=3)
    t2 = start_time.replace(hour=4)
    t3 = start_time.replace(hour=5)

    monitored_entity = "binary_sensor.state"

    def _fake_states(*args, **kwargs):
        return {
            monitored_entity: [
                State(
                    monitored_entity,
                    "on",
                    last_changed=start_time,
                    last_updated=start_time,
                ),
                State(
                    monitored_entity,
                    "off",
                    last_changed=t1,
                    last_updated=t1,
                ),
                State(
                    monitored_entity,
                    "on",
                    last_changed=t2,
                    last_updated=t2,
                ),
            ]
        }

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] is None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_NAME: DEFAULT_NAME,
            CONF_ENTITY_ID: monitored_entity,
            CONF_TYPE: CONF_TYPE_COUNT,
        },
    )
    await hass.async_block_till_done()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_STATE: ["on"],
        },
    )
    await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "options"
    assert result["errors"] is None
    assert result["preview"] == "history_stats"

    with (
        patch(
            "homeassistant.components.recorder.history.state_changes_during_period",
            _fake_states,
        ),
        freeze_time(t3),
    ):
        await client.send_json_auto_id(
            {
                "type": "history_stats/start_preview",
                "flow_id": result["flow_id"],
                "flow_type": "config_flow",
                "user_input": {
                    CONF_ENTITY_ID: monitored_entity,
                    CONF_TYPE: CONF_TYPE_COUNT,
                    CONF_STATE: ["on"],
                    CONF_END: "{{now()}}",
                    CONF_START: "{{ today_at() }}",
                },
            }
        )
        msg = await client.receive_json()
        assert msg["success"]
        assert msg["result"] is None

        msg = await client.receive_json()
        assert msg["event"]["state"] == "2"