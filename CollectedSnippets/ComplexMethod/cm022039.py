async def test_reconfigure_fail(
    hass: HomeAssistant,
    mock_client: MagicMock,
    test_exception: Exception,
    expected_error: str,
) -> None:
    """Test reconfigure errors."""

    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_EMAIL: "test@example.com",
            CONF_PASSWORD: "hunter1",
        },
    )
    entry.add_to_hass(hass)

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": "reconfigure", "entry_id": entry.entry_id}
    )

    assert result["step_id"] == "reconfigure"
    assert result["type"] is FlowResultType.FORM
    assert not result["errors"]

    # Simulate failed login attempt
    mock_client.async_login.side_effect = test_exception

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "hunter1"},
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": expected_error}

    # Retry with a successful login
    mock_client.async_login.side_effect = None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_PASSWORD: "hunter2"},
    )
    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"