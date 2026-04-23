async def test_script_variables_from_coordinator(
    hass: HomeAssistant, calls: list[ServiceCall], caplog: pytest.LogCaptureFixture
) -> None:
    """Test script variables."""
    await async_trigger(hass, "sensor.start", "1")
    with assert_setup_component(1, DOMAIN):
        assert await async_setup_component(
            hass,
            DOMAIN,
            {
                "template": {
                    "variables": {"a": "{{ states('sensor.start') }}", "c": 0},
                    "triggers": {
                        "trigger": "state",
                        "entity_id": ["sensor.trigger"],
                    },
                    "actions": [
                        {
                            "action": "test.automation",
                            "data": {
                                "a": "{{ a }}",
                                "b": "{{ b }}",
                                "c": "{{ c }}",
                            },
                        }
                    ],
                    "sensor": {
                        "name": "test",
                        "state": "{{ 'on' }}",
                        "variables": {"b": "{{ a + 1 }}", "c": 1},
                        "attributes": {
                            "a": "{{ a }}",
                            "b": "{{ b }}",
                            "c": "{{ c }}",
                        },
                    },
                },
            },
        )
    await async_trigger(hass, "sensor.trigger", "anything")

    assert len(calls) == 1
    assert calls[0].data["a"] == 1
    assert calls[0].data["c"] == 0
    assert "'b' is undefined when rendering '{{ b }}'" in caplog.text

    state = hass.states.get("sensor.test")
    assert state
    assert state.state == "on"
    assert state.attributes["a"] == 1
    assert state.attributes["b"] == 2
    assert state.attributes["c"] == 1