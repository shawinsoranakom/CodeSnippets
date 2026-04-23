async def test_options(
    hass: HomeAssistant, platform, unit_prefix_entry: str, unit_prefix_used: str
) -> None:
    """Test reconfiguring and migrated unit prefix."""
    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "name": "My derivative",
            "round": 1.0,
            "source": "sensor.input",
            "time_window": {"seconds": 0.0},
            "unit_prefix": unit_prefix_entry,
            "unit_time": "min",
            "max_sub_interval": {"seconds": 30},
        },
        title="My derivative",
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set("sensor.input", 10, {"unit_of_measurement": "dog"})
    hass.states.async_set("sensor.valid", 10, {"unit_of_measurement": "dog"})
    hass.states.async_set("sensor.invalid", 10, {"unit_of_measurement": "cat"})
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    schema = result["data_schema"].schema
    assert get_schema_suggested_value(schema, "round") == 1.0
    assert get_schema_suggested_value(schema, "time_window") == {"seconds": 0.0}
    assert get_schema_suggested_value(schema, "unit_prefix") == unit_prefix_used
    assert get_schema_suggested_value(schema, "unit_time") == "min"

    source = schema["source"]
    assert isinstance(source, selector.EntitySelector)
    assert source.config["include_entities"] == [
        "sensor.input",
        "sensor.valid",
    ]

    state = hass.states.get(f"{platform}.my_derivative")
    assert state.attributes["unit_of_measurement"] == f"{unit_prefix_used}dog/min"
    hass.states.async_set("sensor.valid", 10, {"unit_of_measurement": "cat"})
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "source": "sensor.valid",
            "round": 2.0,
            "time_window": {"seconds": 10.0},
            "unit_time": "h",
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "name": "My derivative",
        "round": 2.0,
        "source": "sensor.valid",
        "time_window": {"seconds": 10.0},
        "unit_time": "h",
    }
    assert config_entry.data == {}
    assert config_entry.options == {
        "name": "My derivative",
        "round": 2.0,
        "source": "sensor.valid",
        "time_window": {"seconds": 10.0},
        "unit_time": "h",
    }
    assert config_entry.title == "My derivative"

    # Check config entry is reloaded with new options
    await hass.async_block_till_done()

    # Check the entity was updated, no new entity was created
    assert len(hass.states.async_all()) == 4

    # Check the state of the entity has changed as expected
    hass.states.async_set("sensor.valid", 10, {"unit_of_measurement": "cat"})
    hass.states.async_set("sensor.valid", 11, {"unit_of_measurement": "cat"})
    await hass.async_block_till_done()
    state = hass.states.get(f"{platform}.my_derivative")
    assert state.attributes["unit_of_measurement"] == "cat/h"