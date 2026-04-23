async def test_options_flow_preview(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test the options flow preview."""
    logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
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
                State(
                    monitored_entity,
                    "off",
                    last_changed=t2,
                    last_updated=t2,
                ),
            ]
        }

    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            CONF_NAME: DEFAULT_NAME,
            CONF_ENTITY_ID: monitored_entity,
            CONF_TYPE: CONF_TYPE_COUNT,
            CONF_STATE: ["on"],
            CONF_END: "{{ now() }}",
            CONF_START: "{{ today_at() }}",
            CONF_STATE_CLASS: "measurement",
        },
        title=DEFAULT_NAME,
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None
    assert result["preview"] == "history_stats"

    with (
        patch(
            "homeassistant.components.recorder.history.state_changes_during_period",
            _fake_states,
        ),
        freeze_time(t3),
    ):
        for end, exp_count in (
            ("{{now()}}", "2"),
            ("{{today_at('2:00')}}", "1"),
            ("{{today_at('23:00')}}", "2"),
        ):
            await client.send_json_auto_id(
                {
                    "type": "history_stats/start_preview",
                    "flow_id": result["flow_id"],
                    "flow_type": "options_flow",
                    "user_input": {
                        CONF_ENTITY_ID: monitored_entity,
                        CONF_TYPE: CONF_TYPE_COUNT,
                        CONF_STATE: ["on"],
                        CONF_END: end,
                        CONF_START: "{{ today_at() }}",
                        CONF_STATE_CLASS: "measurement",
                    },
                }
            )

            msg = await client.receive_json()
            assert msg["success"]
            assert msg["result"] is None

            msg = await client.receive_json()
            assert msg["event"]["state"] == exp_count

        hass.states.async_set(monitored_entity, "on")

        msg = await client.receive_json()
        assert msg["event"]["state"] == "3"