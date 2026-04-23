async def test_reload_service(hass: HomeAssistant, running) -> None:
    """Verify the reload service."""
    event = "test_event"
    event_flag = asyncio.Event()

    @callback
    def event_handler(event):
        event_flag.set()

    hass.bus.async_listen_once(event, event_handler)
    hass.states.async_set("test.script", "off")

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

    assert hass.states.get(ENTITY_ID) is not None
    assert hass.services.has_service(script.DOMAIN, "test")

    if running != "no":
        _, object_id = split_entity_id(ENTITY_ID)
        await hass.services.async_call(DOMAIN, object_id)
        await asyncio.wait_for(event_flag.wait(), 1)

        assert script.is_on(hass, ENTITY_ID)

    object_id = "test" if running == "same" else "test2"
    with patch(
        "homeassistant.config.load_yaml_config_file",
        return_value={"script": {object_id: {"sequence": [{"delay": {"seconds": 5}}]}}},
    ):
        await hass.services.async_call(DOMAIN, SERVICE_RELOAD, blocking=True)
        await hass.async_block_till_done()

    if running != "same":
        state = hass.states.get(ENTITY_ID)
        assert state.attributes["restored"] is True
        assert not hass.services.has_service(script.DOMAIN, "test")

        assert hass.states.get("script.test2") is not None
        assert hass.services.has_service(script.DOMAIN, "test2")

    else:
        assert hass.states.get(ENTITY_ID) is not None
        assert hass.services.has_service(script.DOMAIN, "test")