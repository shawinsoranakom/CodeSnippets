async def test_config_flow(hass: HomeAssistant, platform) -> None:
    """Test the config flow."""
    input_sensor_entity_id = "sensor.input"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    with patch(
        "homeassistant.components.integration.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "method": "left",
                "name": "My integration",
                "round": 1,
                "source": input_sensor_entity_id,
                "unit_time": "min",
                "max_sub_interval": {"seconds": 0},
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "My integration"
    assert result["data"] == {}
    assert result["options"] == {
        "method": "left",
        "name": "My integration",
        "round": 1.0,
        "source": "sensor.input",
        "unit_time": "min",
        "max_sub_interval": {"seconds": 0},
    }
    assert len(mock_setup_entry.mock_calls) == 1

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert config_entry.data == {}
    assert config_entry.options == {
        "method": "left",
        "name": "My integration",
        "round": 1.0,
        "source": "sensor.input",
        "unit_time": "min",
        "max_sub_interval": {"seconds": 0},
    }
    assert config_entry.title == "My integration"