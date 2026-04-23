async def test_flow_failure(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    raise_error: Exception,
    text_error: str,
) -> None:
    """Test unknown errors."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    with patch(
        "homeassistant.components.lutron.config_flow.Lutron.load_xml_db",
        side_effect=raise_error,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=MOCK_DATA_STEP,
        )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": text_error}

    with (
        patch("homeassistant.components.lutron.config_flow.Lutron.load_xml_db"),
        patch("homeassistant.components.lutron.config_flow.Lutron.guid", "12345678901"),
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input=MOCK_DATA_STEP,
        )

        assert result["type"] is FlowResultType.CREATE_ENTRY
        assert result["result"].title == "Lutron"

        assert result["data"] == MOCK_DATA_STEP