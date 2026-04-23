async def test_config_flow(hass: HomeAssistant, platform: str) -> None:
    """Test the config flow."""
    input_sensors = ["sensor.input_one", "sensor.input_two"]

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    with patch(
        "homeassistant.components.min_max.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"name": "My min_max", "entity_ids": input_sensors, "type": "max"},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "My min_max"
    assert result["data"] == {}
    assert result["options"] == {
        "entity_ids": input_sensors,
        "name": "My min_max",
        "round_digits": 2.0,
        "type": "max",
    }
    assert len(mock_setup_entry.mock_calls) == 1

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert config_entry.data == {}
    assert config_entry.options == {
        "entity_ids": input_sensors,
        "name": "My min_max",
        "round_digits": 2.0,
        "type": "max",
    }
    assert config_entry.title == "My min_max"