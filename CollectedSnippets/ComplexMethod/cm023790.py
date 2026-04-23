async def test_user_flow_flaky(
    hass: HomeAssistant,
    mock_charger: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test user flow create entry with flaky charger."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    mock_charger.test_and_get.side_effect = TimeoutError
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "10.0.0.131"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}

    mock_charger.test_and_get.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_HOST: "10.0.0.131"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "OpenEVSE 10.0.0.131"
    assert result["data"] == {CONF_HOST: "10.0.0.131"}
    assert result["result"].unique_id == "deadbeeffeed"