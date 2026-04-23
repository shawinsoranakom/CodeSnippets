async def test_flow_user_success(
    hass: HomeAssistant, mock_setup_entry: AsyncMock, mock_cookidoo_client: AsyncMock
) -> None:
    """Test we get the user flow and create entry with success."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["handler"] == "cookidoo"

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

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "Cookidoo"
    assert result["data"] == {**MOCK_DATA_USER_STEP, **MOCK_DATA_LANGUAGE_STEP}
    assert len(mock_setup_entry.mock_calls) == 1