async def test_options(hass: HomeAssistant, platform) -> None:
    """Test reconfiguring."""
    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "method": "left",
            "name": "My integration",
            "round": 1.0,
            "source": "sensor.input",
            "unit_prefix": "k",
            "unit_time": "min",
            "max_sub_interval": {"minutes": 1},
        },
        title="My integration",
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    hass.states.async_set("sensor.input", 10, {"unit_of_measurement": "dog"})
    hass.states.async_set("sensor.valid", 10, {"unit_of_measurement": "dog"})
    hass.states.async_set("sensor.invalid", 10, {"unit_of_measurement": "cat"})

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    schema = result["data_schema"].schema
    assert get_schema_suggested_value(schema, "round") == 1.0

    source = schema["source"]
    assert isinstance(source, selector.EntitySelector)
    assert source.config["include_entities"] == [
        "sensor.input",
        "sensor.valid",
    ]

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "method": "right",
            "round": 2.0,
            "source": "sensor.input",
            "max_sub_interval": {"minutes": 1},
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "method": "right",
        "name": "My integration",
        "round": 2.0,
        "source": "sensor.input",
        "unit_prefix": "k",
        "unit_time": "min",
        "max_sub_interval": {"minutes": 1},
    }
    assert config_entry.data == {}
    assert config_entry.options == {
        "method": "right",
        "name": "My integration",
        "round": 2.0,
        "source": "sensor.input",
        "unit_prefix": "k",
        "unit_time": "min",
        "max_sub_interval": {"minutes": 1},
    }
    assert config_entry.title == "My integration"

    # Check config entry is reloaded with new options
    await hass.async_block_till_done()

    # Check the entity was updated, no new entity was created
    assert len(hass.states.async_all()) == 4

    # Check the state of the entity has changed as expected
    hass.states.async_set("sensor.input", 10, {"unit_of_measurement": "dog"})
    hass.states.async_set("sensor.input", 11, {"unit_of_measurement": "dog"})
    await hass.async_block_till_done()

    state = hass.states.get(f"{platform}.my_integration")
    assert state.state != "unknown"
    assert state.attributes["unit_of_measurement"] == "kdogmin"