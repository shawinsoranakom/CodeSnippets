async def test_full_user_flow_with_error(
    hass: HomeAssistant, mock_technove: MagicMock
) -> None:
    """Test the full manual user flow from start to finish with some errors in the middle."""
    mock_technove.update.side_effect = TechnoVEConnectionError
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    assert result.get("step_id") == "user"
    assert result.get("type") is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "192.168.1.123"}
    )

    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "user"
    assert result.get("errors") == {"base": "cannot_connect"}

    mock_technove.update.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_HOST: "192.168.1.123"}
    )

    assert result.get("title") == "TechnoVE Station"
    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert "data" in result
    assert result["data"][CONF_HOST] == "192.168.1.123"
    assert "result" in result
    assert result["result"].unique_id == "AA:AA:AA:AA:AA:BB"