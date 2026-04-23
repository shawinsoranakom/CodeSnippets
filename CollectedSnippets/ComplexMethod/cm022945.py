async def test_concurrent_script(hass: HomeAssistant, concurrently) -> None:
    """Test calling script concurrently or not."""
    if concurrently:
        call_script_2 = {
            "action": "script.turn_on",
            "data": {"entity_id": "script.script2"},
        }
    else:
        call_script_2 = {"action": "script.script2"}
    assert await async_setup_component(
        hass,
        "script",
        {
            "script": {
                "script1": {
                    "mode": "parallel",
                    "sequence": [
                        call_script_2,
                        {
                            "wait_template": "{{ is_state('input_boolean.test1', 'on') }}"
                        },
                        {"action": "test.script", "data": {"value": "script1"}},
                    ],
                },
                "script2": {
                    "mode": "parallel",
                    "sequence": [
                        {"action": "test.script", "data": {"value": "script2a"}},
                        {
                            "wait_template": "{{ is_state('input_boolean.test2', 'on') }}"
                        },
                        {"action": "test.script", "data": {"value": "script2b"}},
                    ],
                },
            }
        },
    )

    service_called = asyncio.Event()
    service_values = []

    async def async_service_handler(service):
        nonlocal service_values
        service_values.append(service.data.get("value"))
        service_called.set()

    hass.services.async_register("test", "script", async_service_handler)
    hass.states.async_set("input_boolean.test1", "off")
    hass.states.async_set("input_boolean.test2", "off")

    await hass.services.async_call("script", "script1")
    await asyncio.wait_for(service_called.wait(), 1)
    service_called.clear()

    assert service_values[-1] == "script2a"
    assert script.is_on(hass, "script.script1")
    assert script.is_on(hass, "script.script2")

    if not concurrently:
        hass.states.async_set("input_boolean.test2", "on")
        await asyncio.wait_for(service_called.wait(), 1)
        service_called.clear()

        assert service_values[-1] == "script2b"

    hass.states.async_set("input_boolean.test1", "on")
    await asyncio.wait_for(service_called.wait(), 1)
    service_called.clear()

    assert service_values[-1] == "script1"
    assert concurrently == script.is_on(hass, "script.script2")

    if concurrently:
        hass.states.async_set("input_boolean.test2", "on")
        await asyncio.wait_for(service_called.wait(), 1)
        service_called.clear()

        assert service_values[-1] == "script2b"

    await hass.async_block_till_done()

    assert not script.is_on(hass, "script.script1")
    assert not script.is_on(hass, "script.script2")