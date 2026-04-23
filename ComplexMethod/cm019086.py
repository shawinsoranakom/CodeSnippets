async def test_config_flow(hass: HomeAssistant, platform) -> None:
    """Test the config flow."""
    input_sensor_entity_id = "sensor.input"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    with patch(
        "homeassistant.components.derivative.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "name": "My derivative",
                "round": 1,
                "source": input_sensor_entity_id,
                "time_window": {"seconds": 0},
                "unit_time": "min",
                "max_sub_interval": {"minutes": 1},
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "My derivative"
    assert result["data"] == {}
    assert result["options"] == {
        "name": "My derivative",
        "round": 1.0,
        "source": "sensor.input",
        "time_window": {"seconds": 0.0},
        "unit_time": "min",
        "max_sub_interval": {"minutes": 1.0},
    }
    assert len(mock_setup_entry.mock_calls) == 1

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert config_entry.data == {}
    assert config_entry.options == {
        "name": "My derivative",
        "round": 1.0,
        "source": "sensor.input",
        "time_window": {"seconds": 0.0},
        "unit_time": "min",
        "max_sub_interval": {"minutes": 1.0},
    }
    assert config_entry.title == "My derivative"