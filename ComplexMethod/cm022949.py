async def test_reload_when_labs_flag_changes(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
) -> None:
    """Test scripts are reloaded when labs flag changes."""
    event = "test_event"
    hass.states.async_set("test.script", "off")

    ws_client = await hass_ws_client(hass)

    assert await async_setup_component(
        hass,
        "script",
        {
            "script": {
                "test": {
                    "sequence": [
                        {"event": event},
                        {"wait_template": "{{ is_state('test.script', 'on') }}"},
                    ]
                }
            }
        },
    )
    assert await async_setup_component(hass, labs.DOMAIN, {})

    assert hass.states.get(ENTITY_ID) is not None
    assert hass.services.has_service(script.DOMAIN, "test")

    for enabled, active_object_id, inactive_object_ids in (
        (False, "test2", ("test",)),
        (True, "test3", ("test", "test2")),
    ):
        with patch(
            "homeassistant.config.load_yaml_config_file",
            return_value={
                "script": {active_object_id: {"sequence": [{"delay": {"seconds": 5}}]}}
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

        for inactive_object_id in inactive_object_ids:
            state = hass.states.get(f"script.{inactive_object_id}")
            assert state.attributes["restored"] is True
            assert not hass.services.has_service(script.DOMAIN, inactive_object_id)

        assert hass.states.get(f"script.{active_object_id}") is not None
        assert hass.services.has_service(script.DOMAIN, active_object_id)