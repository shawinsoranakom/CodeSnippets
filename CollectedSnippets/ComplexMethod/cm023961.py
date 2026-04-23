async def test_full_reauth_flow_implementation(
    hass: HomeAssistant,
    mock_sonarr_config_flow: MagicMock,
    mock_setup_entry: None,
    init_integration: MockConfigEntry,
) -> None:
    """Test the manual reauth flow from start to finish."""
    entry = init_integration

    result = await entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    user_input = MOCK_REAUTH_INPUT.copy()
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input=user_input
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"

    assert entry.data[CONF_API_KEY] == "test-api-key-reauth"