async def test_zeroconf(hass: HomeAssistant) -> None:
    """Test the zeroconf flow."""
    result = await hass.config_entries.flow.async_init(
        thread.DOMAIN, context={"source": "zeroconf"}, data=TEST_ZEROCONF_RECORD
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None
    assert result["step_id"] == "confirm"

    with patch(
        "homeassistant.components.thread.async_setup_entry",
        return_value=True,
    ) as mock_setup_entry:
        result = await hass.config_entries.flow.async_configure(result["flow_id"], {})
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Thread"
    assert result["data"] == {}
    assert result["options"] == {}
    assert len(mock_setup_entry.mock_calls) == 1

    config_entry = hass.config_entries.async_entries(thread.DOMAIN)[0]
    assert config_entry.data == {}
    assert config_entry.options == {}
    assert config_entry.title == "Thread"
    assert config_entry.unique_id is None