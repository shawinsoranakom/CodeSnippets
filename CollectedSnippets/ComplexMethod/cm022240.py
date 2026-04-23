async def test_options(hass: HomeAssistant) -> None:
    """Test reconfiguring."""
    input_sensor = "sensor.input"
    hass.states.async_set(input_sensor, "10")

    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "entity_id": input_sensor,
            "hysteresis": 0.0,
            "lower": -2.0,
            "name": "My threshold",
            "upper": None,
        },
        title="My threshold",
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    schema = result["data_schema"].schema
    assert get_schema_suggested_value(schema, "hysteresis") == 0.0
    assert get_schema_suggested_value(schema, "lower") == -2.0
    assert get_schema_suggested_value(schema, "upper") is None

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "entity_id": input_sensor,
            "hysteresis": 0.0,
            "upper": 20.0,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "entity_id": input_sensor,
        "hysteresis": 0.0,
        "lower": None,
        "name": "My threshold",
        "upper": 20.0,
    }
    assert config_entry.data == {}
    assert config_entry.options == {
        "entity_id": input_sensor,
        "hysteresis": 0.0,
        "lower": None,
        "name": "My threshold",
        "upper": 20.0,
    }
    assert config_entry.title == "My threshold"

    # Check config entry is reloaded with new options
    await hass.async_block_till_done()

    # Check the entity was updated, no new entity was created
    assert len(hass.states.async_all()) == 2

    # Check the state of the entity has changed as expected
    state = hass.states.get("binary_sensor.my_threshold")
    assert state.state == "off"
    assert state.attributes["type"] == "upper"