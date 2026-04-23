async def test_config_flow(hass: HomeAssistant) -> None:
    """Test the config flow."""
    input_sensor = "sensor.input"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    with patch(
        "homeassistant.components.threshold.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "entity_id": input_sensor,
                "lower": -2,
                "upper": 0.0,
                "name": "My threshold sensor",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "My threshold sensor"
    assert result["data"] == {}
    assert result["options"] == {
        "entity_id": input_sensor,
        "hysteresis": 0.0,
        "lower": -2.0,
        "name": "My threshold sensor",
        "upper": 0.0,
    }
    assert len(mock_setup_entry.mock_calls) == 1

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert config_entry.data == {}
    assert config_entry.options == {
        "entity_id": input_sensor,
        "hysteresis": 0.0,
        "lower": -2.0,
        "name": "My threshold sensor",
        "upper": 0.0,
    }
    assert config_entry.title == "My threshold sensor"