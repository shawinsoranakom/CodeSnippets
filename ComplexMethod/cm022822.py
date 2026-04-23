async def test_reauth_failure(
    hass: HomeAssistant,
    mock_setup_entry: AsyncMock,
    config_entry: MockConfigEntry,
    dav_client: Mock,
) -> None:
    """Test a failure during reauthentication configuration flow."""

    config_entry.add_to_hass(hass)

    result = await config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    dav_client.return_value.principal.side_effect = DAVError

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PASSWORD: "password-2",
        },
    )
    await hass.async_block_till_done()

    assert result2.get("type") is FlowResultType.FORM
    assert result2.get("errors") == {"base": "cannot_connect"}

    # Complete the form and it succeeds this time
    dav_client.return_value.principal.side_effect = None
    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PASSWORD: "password-3",
        },
    )
    await hass.async_block_till_done()

    assert result2.get("type") is FlowResultType.ABORT
    assert result2.get("reason") == "reauth_successful"

    # Verify updated configuration entry
    assert dict(config_entry.data) == {
        CONF_URL: "https://example.com/url-1",
        CONF_USERNAME: "username-1",
        CONF_PASSWORD: "password-3",
        CONF_VERIFY_SSL: True,
    }
    assert len(mock_setup_entry.mock_calls) == 1