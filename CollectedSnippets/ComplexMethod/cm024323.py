async def test_form_valid(
    hass: HomeAssistant,
    mock_async_setup_entry: AsyncMock,
) -> None:
    """Test we get the form and the config is created with the good entries."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], TEST_USER_INPUT
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == f"Imeon {TEST_SERIAL}"
    assert result["data"] == TEST_USER_INPUT
    assert result["result"].unique_id == TEST_SERIAL
    assert mock_async_setup_entry.call_count == 1