async def test_config_flow(hass: HomeAssistant, platform) -> None:
    """Test the config flow."""
    input_sensor_entity_id = "sensor.input"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    with patch(
        "homeassistant.components.utility_meter.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "cycle": "monthly",
                "name": "Electricity meter",
                "offset": 0,
                "source": input_sensor_entity_id,
                "tariffs": [],
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Electricity meter"
    assert result["data"] == {}
    assert result["options"] == {
        "cycle": "monthly",
        "delta_values": False,
        "name": "Electricity meter",
        "net_consumption": False,
        "offset": 0,
        "periodically_resetting": True,
        "always_available": False,
        "source": input_sensor_entity_id,
        "tariffs": [],
    }
    assert len(mock_setup_entry.mock_calls) == 1

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert config_entry.data == {}
    assert config_entry.options == {
        "cycle": "monthly",
        "delta_values": False,
        "name": "Electricity meter",
        "net_consumption": False,
        "offset": 0,
        "periodically_resetting": True,
        "always_available": False,
        "source": input_sensor_entity_id,
        "tariffs": [],
    }
    assert config_entry.title == "Electricity meter"