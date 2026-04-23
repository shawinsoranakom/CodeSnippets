async def test_yaml_reload_when_labs_flag_changes(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    hass_admin_user: MockUser,
    hass_read_only_user: MockUser,
) -> None:
    """Test templates are reloaded when labs flag changes."""
    ws_client = await hass_ws_client(hass)

    assert await async_setup_component(
        hass,
        DOMAIN,
        {
            DOMAIN: {
                "triggers": {
                    "trigger": "event",
                    "event_type": "test_event",
                },
                "sensor": {
                    "name": "hello",
                    "state": "{{ trigger.event.data.stuff }}",
                },
            }
        },
    )
    assert await async_setup_component(hass, labs.DOMAIN, {})
    assert hass.states.get("sensor.hello") is not None
    assert hass.states.get("sensor.bye") is None
    listeners = hass.bus.async_listeners()
    assert listeners.get("test_event") == 1
    assert listeners.get("test_event2") is None

    context = Context()
    hass.bus.async_fire("test_event", {"stuff": "foo"}, context=context)
    await hass.async_block_till_done()
    assert hass.states.get("sensor.hello").state == "foo"

    test_reload_event = async_capture_events(hass, "event_template_reloaded")

    # Check we reload whenever the labs flag is set, even if it's already enabled
    last_state = "unknown"
    for enabled, set_state in (
        (True, "foo"),
        (True, "bar"),
        (False, "beer"),
        (False, "good"),
    ):
        test_reload_event.clear()

        with patch(
            "homeassistant.config.load_yaml_config_file",
            autospec=True,
            return_value={
                DOMAIN: {
                    "triggers": {
                        "trigger": "event",
                        "event_type": "test_event2",
                    },
                    "sensor": {
                        "name": "bye",
                        "state": "{{ trigger.event.data.stuff }}",
                    },
                }
            },
        ):
            await ws_client.send_json_auto_id(
                {
                    "type": "labs/update",
                    "domain": "automation",
                    "preview_feature": "new_triggers_conditions",
                    "enabled": enabled,
                }
            )

            msg = await ws_client.receive_json()
            assert msg["success"]
            await hass.async_block_till_done()

        assert len(test_reload_event) == 1

        assert hass.states.get("sensor.hello") is None
        assert hass.states.get("sensor.bye") is not None
        listeners = hass.bus.async_listeners()
        assert listeners.get("test_event") is None
        assert listeners.get("test_event2") == 1

        hass.bus.async_fire("test_event", {"stuff": "foo"}, context=context)
        await hass.async_block_till_done()
        assert hass.states.get("sensor.bye").state == last_state

        hass.bus.async_fire("test_event2", {"stuff": set_state}, context=context)
        await hass.async_block_till_done()
        assert hass.states.get("sensor.bye").state == set_state
        last_state = set_state