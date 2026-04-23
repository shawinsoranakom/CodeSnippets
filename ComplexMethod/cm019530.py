async def test_reauth(
    hass: HomeAssistant,
    mock_added_config_entry: MockConfigEntry,
    mock_setup_entry: AsyncMock,
    mock_ring_auth: Mock,
) -> None:
    """Test reauth flow."""
    mock_added_config_entry.async_start_reauth(hass)
    await hass.async_block_till_done()

    flows = hass.config_entries.flow.async_progress()
    assert len(flows) == 1
    [result] = flows
    assert result["step_id"] == "reauth_confirm"

    mock_ring_auth.async_fetch_token.side_effect = ring_doorbell.Requires2FAError
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={
            CONF_PASSWORD: "other_fake_password",
        },
    )

    mock_ring_auth.async_fetch_token.assert_called_once_with(
        "foo@bar.com", "other_fake_password", None
    )
    assert result2["type"] is FlowResultType.FORM
    assert result2["step_id"] == "2fa"
    mock_ring_auth.async_fetch_token.reset_mock(side_effect=True)
    mock_ring_auth.async_fetch_token.return_value = "new-foobar"
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={"2fa": "123456"},
    )

    mock_ring_auth.async_fetch_token.assert_called_once_with(
        "foo@bar.com", "other_fake_password", "123456"
    )
    assert result3["type"] is FlowResultType.ABORT
    assert result3["reason"] == "reauth_successful"
    assert mock_added_config_entry.data == {
        CONF_DEVICE_ID: MOCK_HARDWARE_ID,
        CONF_USERNAME: "foo@bar.com",
        CONF_TOKEN: "new-foobar",
    }
    assert len(mock_setup_entry.mock_calls) == 1