async def test_trigger_attribute_order(
    hass: HomeAssistant, caplog: pytest.LogCaptureFixture
) -> None:
    """Test trigger entity attributes order."""
    assert await async_setup_component(
        hass,
        "template",
        {
            "template": [
                {
                    "trigger": {"platform": "event", "event_type": "test_event"},
                    "sensor": [
                        {
                            "name": "Test Sensor",
                            "availability": "{{ trigger and trigger.event.data.beer == 2 }}",
                            "state": "{{ trigger.event.data.beer }}",
                            "attributes": {
                                "beer": "{{ trigger.event.data.beer }}",
                                "no_beer": "{{ sad - 1 }}",
                                "more_beer": "{{ beer + 1 }}",
                                "all_the_beer": "{{ this.state | int + more_beer }}",
                            },
                        },
                    ],
                },
            ],
        },
    )

    await hass.async_block_till_done()

    # Sensors are unknown if never triggered
    state = hass.states.get("sensor.test_sensor")
    assert state is not None
    assert state.state == STATE_UNKNOWN

    hass.bus.async_fire("test_event", {"beer": 2})
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test_sensor")
    assert state.state == "2"

    assert state.attributes["beer"] == 2
    assert "no_beer" not in state.attributes
    assert (
        "Error rendering attributes.no_beer template for sensor.test_sensor: UndefinedError: 'sad' is undefined"
        in caplog.text
    )
    assert state.attributes["more_beer"] == 3
    assert (
        "Error rendering attributes.all_the_beer template for sensor.test_sensor: ValueError: Template error: int got invalid input 'unknown' when rendering template '{{ this.state | int + more_beer }}' but no default was specified"
        in caplog.text
    )

    hass.bus.async_fire("test_event", {"beer": 2})
    await hass.async_block_till_done()

    state = hass.states.get("sensor.test_sensor")
    assert state.state == "2"

    assert state.attributes["beer"] == 2
    assert state.attributes["more_beer"] == 3
    assert state.attributes["all_the_beer"] == 5

    assert (
        caplog.text.count(
            "Error rendering attributes.no_beer template for sensor.test_sensor: UndefinedError: 'sad' is undefined"
        )
        == 2
    )