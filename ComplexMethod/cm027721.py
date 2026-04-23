async def test_config_flow(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, platform
) -> None:
    """Test the config flow."""
    input_sensor_entity_id = "sensor.input"

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"name": "My NEW_DOMAIN", "entity_id": input_sensor_entity_id},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "My NEW_DOMAIN"
    assert result["data"] == {}
    assert result["options"] == {
        "entity_id": input_sensor_entity_id,
        "name": "My NEW_DOMAIN",
    }
    assert len(mock_setup_entry.mock_calls) == 1

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert config_entry.data == {}
    assert config_entry.options == {
        "entity_id": input_sensor_entity_id,
        "name": "My NEW_DOMAIN",
    }
    assert config_entry.title == "My NEW_DOMAIN"