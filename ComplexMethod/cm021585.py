async def test_reload_when_labs_flag_changes(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    calls: list[ServiceCall],
    hass_admin_user: MockUser,
    hass_read_only_user: MockUser,
) -> None:
    """Test automations are reloaded when labs flag changes."""
    ws_client = await hass_ws_client(hass)

    assert await async_setup_component(
        hass,
        automation.DOMAIN,
        {
            automation.DOMAIN: {
                "alias": "hello",
                "trigger": {"platform": "event", "event_type": "test_event"},
                "action": {
                    "action": "test.automation",
                    "data_template": {"event": "{{ trigger.event.event_type }}"},
                },
            }
        },
    )
    assert await async_setup_component(hass, labs.DOMAIN, {})
    assert hass.states.get("automation.hello") is not None
    assert hass.states.get("automation.bye") is None
    listeners = hass.bus.async_listeners()
    assert listeners.get("test_event") == 1
    assert listeners.get("test_event2") is None

    hass.bus.async_fire("test_event")
    await hass.async_block_till_done()

    assert len(calls) == 1
    assert calls[0].data.get("event") == "test_event"

    test_reload_event = async_capture_events(hass, EVENT_AUTOMATION_RELOADED)

    # Check we reload whenever the labs flag is set, even if it's already enabled
    for enabled in (True, True, False, False):
        test_reload_event.clear()
        calls.clear()

        with patch(
            "homeassistant.config.load_yaml_config_file",
            autospec=True,
            return_value={
                automation.DOMAIN: {
                    "alias": "bye",
                    "trigger": {"platform": "event", "event_type": "test_event2"},
                    "action": {
                        "action": "test.automation",
                        "data_template": {"event": "{{ trigger.event.event_type }}"},
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

        assert hass.states.get("automation.hello") is None
        assert hass.states.get("automation.bye") is not None
        listeners = hass.bus.async_listeners()
        assert listeners.get("test_event") is None
        assert listeners.get("test_event2") == 1

        hass.bus.async_fire("test_event")
        await hass.async_block_till_done()
        assert len(calls) == 0

        hass.bus.async_fire("test_event2")
        await hass.async_block_till_done()
        assert len(calls) == 1
        assert calls[-1].data.get("event") == "test_event2"