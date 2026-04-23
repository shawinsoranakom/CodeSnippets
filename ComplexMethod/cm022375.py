async def test_full_flow(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "10.0.0.131"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Outdoor Smart Plug (WPO-01)"
    assert result["data"] == {
        CONF_HOST: "10.0.0.131",
        CONF_NAME: "Outdoor Smart Plug",
        CONF_DEVICE_ID: "aabbccddee02",
        CONF_MODEL: "WPO-01",
    }
    assert result["result"].unique_id == "aabbccddee02"
    assert len(mock_setup_entry.mock_calls) == 1