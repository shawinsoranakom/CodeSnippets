async def test_options_flow_preview_errors(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test the options flow preview."""
    logging.getLogger("sqlalchemy.engine").setLevel(logging.ERROR)
    client = await hass_ws_client(hass)

    # add state for the tests
    monitored_entity = "binary_sensor.state"

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

    for schema in (
        {CONF_END: "{{ now() }"},  # Missing '}' at end of template
        {CONF_START: "{{ today_at( }}"},  # Missing ')' in template function
        {CONF_DURATION: {"hours": 1}},  # Specified 3 period keys (1 too many)
        {CONF_START: ""},  # Specified 1 period keys (1 too few)
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
                    CONF_END: "{{ now() }}",
                    CONF_START: "{{ today_at() }}",
                    **schema,
                },
            }
        )

        msg = await client.receive_json()
        assert not msg["success"]
        assert msg["error"]["code"] == "invalid_schema"

    for schema in (
        {CONF_END: "{{ nowwww() }}"},  # Unknown jinja function
        {CONF_START: "{{ today_at('abcde') }}"},  # Invalid value passed to today_at
        {CONF_END: '"{{ now() }}"'},  # Invalid quotes around template
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
                    CONF_END: "{{ now() }}",
                    CONF_START: "{{ today_at() }}",
                    **schema,
                },
            }
        )

        msg = await client.receive_json()
        assert msg["success"]
        assert msg["result"] is None

        msg = await client.receive_json()
        assert msg["event"]["error"]