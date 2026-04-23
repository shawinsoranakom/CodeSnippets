async def test_async_step_user_errors(
    hass: HomeAssistant,
    mock_pynecil: AsyncMock,
    raise_error: Exception,
    text_error: str,
) -> None:
    """Test the user config flow errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    mock_pynecil.connect.side_effect = raise_error
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": text_error}

    mock_pynecil.connect.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        USER_INPUT,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == DEFAULT_NAME
    assert result["data"] == {}
    assert result["result"].unique_id == "c0:ff:ee:c0:ff:ee"