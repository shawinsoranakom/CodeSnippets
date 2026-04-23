async def test_form_2fa(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    mock_ring_auth: Mock,
) -> None:
    """Test form flow for 2fa."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    mock_ring_auth.async_fetch_token.side_effect = ring_doorbell.Requires2FAError
    with patch("uuid.uuid4", return_value=MOCK_HARDWARE_ID):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "foo@bar.com",
                CONF_PASSWORD: "fake-password",
            },
        )
    await hass.async_block_till_done()
    mock_ring_auth.async_fetch_token.assert_called_once_with(
        "foo@bar.com", "fake-password", None
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
        "foo@bar.com", "fake-password", "123456"
    )
    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["title"] == "foo@bar.com"
    assert result3["data"] == {
        CONF_DEVICE_ID: MOCK_HARDWARE_ID,
        CONF_USERNAME: "foo@bar.com",
        CONF_TOKEN: "new-foobar",
    }
    assert len(mock_setup_entry.mock_calls) == 1