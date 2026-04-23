async def test_form_invalid_auth(hass: HomeAssistant) -> None:
    """Test we handle invalid auth."""
    init_result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(GET_GATEWAY_HISTORY_DATA, side_effect=InvalidAuth):
        config_result = await hass.config_entries.flow.async_configure(
            init_result["flow_id"],
            BASE_DATA,
        )

    assert config_result["type"] is FlowResultType.FORM
    assert config_result["errors"] == {"base": "invalid_auth"}

    # Check that we still can finalize setup
    with patch_gateway_ok(), patch_setup_entry_ok() as mock_setup_entry:
        config_result = await hass.config_entries.flow.async_configure(
            init_result["flow_id"],
            BASE_DATA,
        )
        await hass.async_block_till_done()
    assert config_result["type"] is FlowResultType.CREATE_ENTRY
    assert config_result["title"] == EXPECTED_TITLE
    assert config_result["data"] == BASE_DATA
    assert config_result["context"]["unique_id"] == GATEWAY_MAC_LOWER
    assert len(mock_setup_entry.mock_calls) == 1