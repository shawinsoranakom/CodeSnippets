async def test_form_valid_reauth_with_totp(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_unload_entry: AsyncMock,
) -> None:
    """Test that we can handle a valid reauth for a utility with TOTP."""
    mock_config_entry = MockConfigEntry(
        title="Consolidated Edison (ConEd) (test-username)",
        domain=DOMAIN,
        data={
            "utility": "Consolidated Edison (ConEd)",
            "username": "test-username",
            "password": "test-password",
        },
    )
    mock_config_entry.add_to_hass(hass)
    mock_config_entry.mock_state(hass, ConfigEntryState.LOADED)
    hass.config.components.add(DOMAIN)
    mock_config_entry.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    result = flows[0]

    with patch(
        "homeassistant.components.opower.config_flow.Opower.async_login",
        side_effect=InvalidAuth,
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])
        assert result["data_schema"].schema.keys() == {
            "username",
            "password",
            "totp_secret",
        }

    with patch(
        "homeassistant.components.opower.config_flow.Opower.async_login",
    ) as mock_login:
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                "username": "test-username",
                "password": "test-password2",
                "totp_secret": "test-totp",
            },
        )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"

    await hass.async_block_till_done()
    assert mock_config_entry.data == {
        "utility": "Consolidated Edison (ConEd)",
        "username": "test-username",
        "password": "test-password2",
        "totp_secret": "test-totp",
    }
    assert len(mock_unload_entry.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1
    assert mock_login.call_count == 1