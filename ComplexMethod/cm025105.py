async def test_lifecycle(hass: HomeAssistant) -> None:
    """Test that we limit template render info for lifecycle events."""
    hass.states.async_set("sun.sun", "above", {"elevation": 50, "next_rising": "later"})
    for i in range(2):
        hass.states.async_set(f"sensor.sensor{i}", "on")
    hass.states.async_set("sensor.removed", "off")

    await hass.async_block_till_done()

    hass.states.async_set("sun.sun", "below", {"elevation": 60, "next_rising": "later"})
    for i in range(2):
        hass.states.async_set(f"sensor.sensor{i}", "off")

    hass.states.async_set("sensor.new", "off")
    hass.states.async_remove("sensor.removed")

    await hass.async_block_till_done()

    info = render_to_info(hass, "{{ states | count }}")
    assert info.all_states is False
    assert info.all_states_lifecycle is True
    assert info.rate_limit is None
    assert info.has_time is False

    assert info.entities == set()
    assert info.domains == set()
    assert info.domains_lifecycle == set()

    assert info.filter("sun.sun") is False
    assert info.filter("sensor.sensor1") is False
    assert info.filter_lifecycle("sensor.new") is True
    assert info.filter_lifecycle("sensor.removed") is True