async def test_ok_setup(hass: HomeAssistant, init_data, init_context, entry) -> None:
    """Test we get the form."""
    init_result = await hass.config_entries.flow.async_init(
        DOMAIN,
        data=init_data,
        context=init_context,
    )
    assert init_result["type"] is FlowResultType.FORM
    assert init_result["step_id"] == config_entries.SOURCE_USER
    assert init_result["errors"] is None

    # Check that we can finalize setup
    with patch_gateway_ok(), patch_setup_entry_ok() as mock_setup_entry:
        config_result = await hass.config_entries.flow.async_configure(
            init_result["flow_id"],
            entry,
        )
        await hass.async_block_till_done()
    assert config_result["type"] is FlowResultType.CREATE_ENTRY
    assert config_result["title"] == EXPECTED_TITLE
    assert config_result["data"] == entry
    assert config_result["context"]["unique_id"] == GATEWAY_MAC_LOWER
    assert len(mock_setup_entry.mock_calls) == 1