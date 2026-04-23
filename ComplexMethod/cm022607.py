async def test_config_flow(hass: HomeAssistant, platform) -> None:
    """Test the config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    with patch(
        "homeassistant.components.tod.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "after_time": "10:00",
                "before_time": "18:00",
                "name": "My tod",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "My tod"
    assert result["data"] == {}
    assert result["options"] == {
        "after_time": "10:00",
        "before_time": "18:00",
        "name": "My tod",
    }
    assert len(mock_setup_entry.mock_calls) == 1

    config_entry = hass.config_entries.async_entries(DOMAIN)[0]
    assert config_entry.data == {}
    assert config_entry.options == {
        "after_time": "10:00",
        "before_time": "18:00",
        "name": "My tod",
    }
    assert config_entry.title == "My tod"