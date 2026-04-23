async def test_manual_flow_creates_entry(
    hass: HomeAssistant,
    ap_status_fixture: dict[str, Any],
    mock_airos_client: AsyncMock,
    mock_async_get_firmware_data: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test we get the user form and create the appropriate entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN,
        context={"source": SOURCE_USER},
    )

    assert result["type"] is FlowResultType.MENU
    assert "manual" in result["menu_options"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {"next_step_id": "manual"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], MOCK_CONFIG
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "NanoStation 5AC ap name"
    assert result["result"].unique_id == "01:23:45:67:89:AB"
    assert result["data"] == MOCK_CONFIG
    assert len(mock_setup_entry.mock_calls) == 1