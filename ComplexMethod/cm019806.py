async def test_form_advanced(hass: HomeAssistant, mock_setup_entry: AsyncMock) -> None:
    """Test we get the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.MENU
    assert "advanced" in result["menu_options"]
    assert result["step_id"] == "user"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {"next_step_id": "advanced"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}
    assert result["step_id"] == "advanced"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=MOCK_DATA_ADVANCED_STEP,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "test-user"
    assert result["data"] == {
        CONF_API_USER: TEST_API_USER,
        CONF_API_KEY: TEST_API_KEY,
        CONF_URL: DEFAULT_URL,
        CONF_VERIFY_SSL: True,
    }
    assert result["result"].unique_id == TEST_API_USER

    assert len(mock_setup_entry.mock_calls) == 1