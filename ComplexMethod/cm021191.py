async def test_reauth_flow(
    hass: HomeAssistant,
    mock_config_entry: MockConfigEntry,
    mock_pvoutput: MagicMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test the reauthentication configuration flow."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reauth_flow(hass)
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "reauth_confirm"

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_API_KEY: "some_new_key"},
    )
    await hass.async_block_till_done()

    assert result2.get("type") is FlowResultType.ABORT
    assert result2.get("reason") == "reauth_successful"
    assert mock_config_entry.data == {
        CONF_SYSTEM_ID: 12345,
        CONF_API_KEY: "some_new_key",
    }

    assert len(mock_setup_entry.mock_calls) == 1
    assert len(mock_pvoutput.system.mock_calls) == 1