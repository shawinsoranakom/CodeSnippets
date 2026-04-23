async def test_flow_user_init_data_unknown_error_and_recover_on_step_2(
    hass: HomeAssistant,
    mock_cookidoo_client: AsyncMock,
    raise_error: Exception,
    text_error: str,
) -> None:
    """Test unknown errors."""
    mock_cookidoo_client.get_additional_items.side_effect = raise_error

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_DATA_USER_STEP,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "language"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_DATA_LANGUAGE_STEP,
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == text_error

    # Recover
    mock_cookidoo_client.get_additional_items.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_DATA_LANGUAGE_STEP,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].title == "Cookidoo"

    assert result["data"] == {**MOCK_DATA_USER_STEP, **MOCK_DATA_LANGUAGE_STEP}