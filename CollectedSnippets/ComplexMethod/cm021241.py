async def test_form_single_site(
    hass: HomeAssistant,
    mock_omada_client: MagicMock,
    mock_setup_entry: MagicMock,
) -> None:
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_USER_DATA,
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "OC200 (Display Name)"
    assert result["data"] == MOCK_ENTRY_DATA
    assert result["result"].unique_id == "12345"
    assert len(mock_setup_entry.mock_calls) == 1