async def test_options(hass: HomeAssistant) -> None:
    """Test reconfiguring."""
    input_sensor1_entity_id = "sensor.input1"
    input_sensor2_entity_id = "sensor.input2"

    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "cycle": "monthly",
            "delta_values": False,
            "name": "Electricity meter",
            "net_consumption": False,
            "offset": 0,
            "periodically_resetting": True,
            "source": input_sensor1_entity_id,
            "tariffs": "",
        },
        title="Electricity meter",
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    schema = result["data_schema"].schema
    assert get_schema_suggested_value(schema, "source") == input_sensor1_entity_id
    assert get_schema_suggested_value(schema, "periodically_resetting") is True

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "source": input_sensor2_entity_id,
            "periodically_resetting": False,
            "always_available": True,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "cycle": "monthly",
        "delta_values": False,
        "name": "Electricity meter",
        "net_consumption": False,
        "offset": 0,
        "periodically_resetting": False,
        "always_available": True,
        "source": input_sensor2_entity_id,
        "tariffs": "",
    }
    assert config_entry.data == {}
    assert config_entry.options == {
        "cycle": "monthly",
        "delta_values": False,
        "name": "Electricity meter",
        "net_consumption": False,
        "offset": 0,
        "periodically_resetting": False,
        "always_available": True,
        "source": input_sensor2_entity_id,
        "tariffs": "",
    }
    assert config_entry.title == "Electricity meter"

    # Check config entry is reloaded with new options
    await hass.async_block_till_done()