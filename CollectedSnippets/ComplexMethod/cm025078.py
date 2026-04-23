async def test_track_template_result_complex(hass: HomeAssistant) -> None:
    """Test tracking template."""
    specific_runs = []
    template_complex_str = """
{% if states("sensor.domain") == "light" %}
  {{ states.light | map(attribute='entity_id') | list }}
{% elif states("sensor.domain") == "lock" %}
  {{ states.lock | map(attribute='entity_id') | list }}
{% elif states("sensor.domain") == "single_binary_sensor" %}
  {{ states("binary_sensor.single") }}
{% else %}
  {{ states | map(attribute='entity_id') | list }}
{% endif %}

"""
    template_complex = Template(template_complex_str, hass)

    def specific_run_callback(
        event: Event[EventStateChangedData] | None,
        updates: list[TrackTemplateResult],
    ) -> None:
        specific_runs.append(updates.pop().result)

    hass.states.async_set("light.one", "on")
    hass.states.async_set("lock.one", "locked")

    info = async_track_template_result(
        hass,
        [TrackTemplate(template_complex, None, 0)],
        specific_run_callback,
    )
    await hass.async_block_till_done()

    assert info.listeners == {
        "all": True,
        "domains": set(),
        "entities": set(),
        "time": False,
    }

    hass.states.async_set("sensor.domain", "light")
    await hass.async_block_till_done()
    assert len(specific_runs) == 1
    assert specific_runs[0] == ["light.one"]

    assert info.listeners == {
        "all": False,
        "domains": {"light"},
        "entities": {"sensor.domain"},
        "time": False,
    }

    hass.states.async_set("sensor.domain", "lock")
    await hass.async_block_till_done()
    assert len(specific_runs) == 2
    assert specific_runs[1] == ["lock.one"]
    assert info.listeners == {
        "all": False,
        "domains": {"lock"},
        "entities": {"sensor.domain"},
        "time": False,
    }

    hass.states.async_set("sensor.domain", "all")
    await hass.async_block_till_done()
    assert len(specific_runs) == 3
    assert "light.one" in specific_runs[2]
    assert "lock.one" in specific_runs[2]
    assert "sensor.domain" in specific_runs[2]
    assert info.listeners == {
        "all": True,
        "domains": set(),
        "entities": set(),
        "time": False,
    }

    hass.states.async_set("sensor.domain", "light")
    await hass.async_block_till_done()
    assert len(specific_runs) == 4
    assert specific_runs[3] == ["light.one"]
    assert info.listeners == {
        "all": False,
        "domains": {"light"},
        "entities": {"sensor.domain"},
        "time": False,
    }

    hass.states.async_set("light.two", "on")
    await hass.async_block_till_done()
    assert len(specific_runs) == 5
    assert "light.one" in specific_runs[4]
    assert "light.two" in specific_runs[4]
    assert "sensor.domain" not in specific_runs[4]
    assert info.listeners == {
        "all": False,
        "domains": {"light"},
        "entities": {"sensor.domain"},
        "time": False,
    }

    hass.states.async_set("light.three", "on")
    await hass.async_block_till_done()
    assert len(specific_runs) == 6
    assert "light.one" in specific_runs[5]
    assert "light.two" in specific_runs[5]
    assert "light.three" in specific_runs[5]
    assert "sensor.domain" not in specific_runs[5]
    assert info.listeners == {
        "all": False,
        "domains": {"light"},
        "entities": {"sensor.domain"},
        "time": False,
    }

    hass.states.async_set("sensor.domain", "lock")
    await hass.async_block_till_done()
    assert len(specific_runs) == 7
    assert specific_runs[6] == ["lock.one"]
    assert info.listeners == {
        "all": False,
        "domains": {"lock"},
        "entities": {"sensor.domain"},
        "time": False,
    }

    hass.states.async_set("sensor.domain", "single_binary_sensor")
    await hass.async_block_till_done()
    assert len(specific_runs) == 8
    assert specific_runs[7] == "unknown"
    assert info.listeners == {
        "all": False,
        "domains": set(),
        "entities": {"binary_sensor.single", "sensor.domain"},
        "time": False,
    }

    hass.states.async_set("binary_sensor.single", "on")
    await hass.async_block_till_done()
    assert len(specific_runs) == 9
    assert specific_runs[8] == "on"
    assert info.listeners == {
        "all": False,
        "domains": set(),
        "entities": {"binary_sensor.single", "sensor.domain"},
        "time": False,
    }

    hass.states.async_set("sensor.domain", "lock")
    await hass.async_block_till_done()
    assert len(specific_runs) == 10
    assert specific_runs[9] == ["lock.one"]
    assert info.listeners == {
        "all": False,
        "domains": {"lock"},
        "entities": {"sensor.domain"},
        "time": False,
    }