async def test_form_valid_reauth(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_unload_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test that we can handle a valid reauth."""
    mock_config_entry.mock_state(hass, ConfigEntryState.LOADED)
    hass.config.components.add(DOMAIN)
    mock_config_entry.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    result = flows[0]
    assert result["step_id"] == "reauth_confirm"
    assert result["context"]["source"] == "reauth"
    assert result["context"]["title_placeholders"] == {"name": mock_config_entry.title}

    with patch(
        "homeassistant.components.opower.config_flow.Opower.async_login",
        side_effect=InvalidAuth,
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        assert result["data_schema"].schema.keys() == {
            "username",
            "password",
        }

    with patch(
        "homeassistant.components.opower.config_flow.Opower.async_login",
    ) as mock_login:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {"username": "test-username", "password": "test-password2"},
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"

    await hass.async_block_till_done()
    assert mock_config_entry.data == {
        "utility": "Pacific Gas and Electric Company (PG&E)",
        "username": "test-username",
        "password": "test-password2",
    }
    assert len(mock_unload_entry.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1
    assert mock_login.call_count == 1