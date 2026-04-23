async def test_reauth_errors(
    hass: HomeAssistant,
    config_entry: MockConfigEntry,
    mock_namecheap: AsyncMock,
    side_effect: Exception | bool,
    text_error: str,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test we handle errors."""
    aioclient_mock.get(
        UPDATE_URL,
        params=TEST_USER_INPUT,
        text="<interface-response><ErrCount>0</ErrCount></interface-response>",
    )
    config_entry.add_to_hass(hass)
    assert await hass.config_entries.async_setup(config_entry.entry_id)
    await hass.async_block_till_done()

    assert config_entry.state is ConfigEntryState.LOADED

    result = await config_entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    mock_namecheap.side_effect = [side_effect]
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new-password"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": text_error}

    mock_namecheap.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], {CONF_PASSWORD: "new-password"}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"

    assert config_entry.data[CONF_PASSWORD] == "new-password"