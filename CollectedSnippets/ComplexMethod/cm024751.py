async def test_reauth(
    hass: HomeAssistant, mock_setup_entry, mock_config_entry: MockConfigEntry, mock_tv
) -> None:
    """Test we get the form."""

    mock_tv.system = MOCK_SYSTEM | {"model": "changed"}

    assert await hass.config_entries.async_setup(mock_config_entry.entry_id)
    assert len(mock_setup_entry.mock_calls) == 1

    result = await mock_config_entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        MOCK_USERINPUT,
    )
    await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.ABORT
    assert result2["reason"] == "reauth_successful"
    assert mock_config_entry.data == MOCK_CONFIG | {"system": mock_tv.system}
    assert len(mock_setup_entry.mock_calls) == 2