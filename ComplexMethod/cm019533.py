async def test_reconfigure_errors(
    hass: HomeAssistant,
    mock_added_config_entry: MockConfigEntry,
    mock_setup_entry: AsyncMock,
    mock_ring_auth: Mock,
    error_type,
    errors_msg,
) -> None:
    """Test errors during the reconfigure config flow."""
    result = await mock_added_config_entry.start_reconfigure_flow(hass)
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    mock_ring_auth.async_fetch_token.side_effect = error_type
    with patch("uuid.uuid4", return_value="new-hardware-id"):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            user_input={
                CONF_PASSWORD: "error_fake_password",
            },
        )
    await hass.async_block_till_done()
    mock_ring_auth.async_fetch_token.assert_called_with(
        "foo@bar.com", "error_fake_password", None
    )
    mock_ring_auth.async_fetch_token.side_effect = ring_doorbell.Requires2FAError
    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input={
            CONF_PASSWORD: "other_fake_password",
        },
    )

    mock_ring_auth.async_fetch_token.assert_called_with(
        "foo@bar.com", "other_fake_password", None
    )
    assert result3["type"] is FlowResultType.FORM
    assert result3["step_id"] == "2fa"

    # Now test reconfigure can go on to succeed
    mock_ring_auth.async_fetch_token.reset_mock(side_effect=True)
    mock_ring_auth.async_fetch_token.return_value = "new-foobar"

    result4 = await hass.config_entries.flow.async_configure(
        result3["flow_id"],
        user_input={"2fa": "123456"},
    )

    mock_ring_auth.async_fetch_token.assert_called_with(
        "foo@bar.com", "other_fake_password", "123456"
    )

    assert result4["type"] is FlowResultType.ABORT
    assert result4["reason"] == "reconfigure_successful"
    assert mock_added_config_entry.data == {
        CONF_DEVICE_ID: "new-hardware-id",
        CONF_USERNAME: "foo@bar.com",
        CONF_TOKEN: "new-foobar",
    }
    assert len(mock_setup_entry.mock_calls) == 1