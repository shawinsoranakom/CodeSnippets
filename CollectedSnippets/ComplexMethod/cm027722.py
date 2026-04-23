async def test_options(hass: HomeAssistant, platform) -> None:
    """Test reconfiguring."""
    input_sensor_1_entity_id = "sensor.input1"
    input_sensor_2_entity_id = "sensor.input2"

    # Setup the config entry
    config_entry = MockConfigEntry(
        data={},
        domain=DOMAIN,
        options={
            "entity_id": input_sensor_1_entity_id,
            "name": "My NEW_DOMAIN",
        },
        title="My NEW_DOMAIN",
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    result = await hass.config_entries.options.async_init(config_entry.entry_id)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "init"
    schema = result["data_schema"].schema
    assert get_suggested(schema, "entity_id") == input_sensor_1_entity_id

    result = await hass.config_entries.options.async_configure(
        result["flow_id"],
        user_input={
            "entity_id": input_sensor_2_entity_id,
        },
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["data"] == {
        "entity_id": input_sensor_2_entity_id,
        "name": "My NEW_DOMAIN",
    }
    assert config_entry.data == {}
    assert config_entry.options == {
        "entity_id": input_sensor_2_entity_id,
        "name": "My NEW_DOMAIN",
    }
    assert config_entry.title == "My NEW_DOMAIN"

    # Check config entry is reloaded with new options
    await hass.async_block_till_done()

    # Check the entity was updated, no new entity was created
    assert len(hass.states.async_all()) == 1

    # TODO Check the state of the entity has changed as expected
    state = hass.states.get(f"{platform}.my_NEW_DOMAIN")
    assert state.attributes == {}