async def test_flow_reconfigure(
    hass: HomeAssistant,
    mock_aiontfy: AsyncMock,
    entry_data: dict[str, str | None],
    user_input: dict[str, str],
    step_id: str,
) -> None:
    """Test reconfigure flow."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        title="ntfy.sh",
        data={
            CONF_URL: "https://ntfy.sh/",
            **entry_data,
        },
    )
    mock_aiontfy.generate_token.return_value = AccountTokenResponse(
        token="newtoken", last_access=datetime.now()
    )
    config_entry.add_to_hass(hass)
    result = await config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == step_id

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input,
    )

    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert config_entry.data[CONF_USERNAME] == "username"
    assert config_entry.data[CONF_TOKEN] == "newtoken"

    assert len(hass.config_entries.async_entries()) == 1