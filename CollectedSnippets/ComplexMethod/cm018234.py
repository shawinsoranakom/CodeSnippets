async def test_reconfigure_error_and_recover(
    hass: HomeAssistant,
    ista_config_entry: MockConfigEntry,
    mock_ista: MagicMock,
    side_effect: Exception,
    error_text: str,
) -> None:
    """Test reconfigure flow error and recover."""

    ista_config_entry.add_to_hass(hass)

    result = await ista_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    mock_ista.login.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "new@example.com",
            CONF_PASSWORD: "new-password",
        },
    )

    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {"base": error_text}

    mock_ista.login.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_EMAIL: "new@example.com",
            CONF_PASSWORD: "new-password",
        },
    )

    await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert ista_config_entry.data == {
        CONF_EMAIL: "new@example.com",
        CONF_PASSWORD: "new-password",
    }
    assert len(hass.config_entries.async_entries()) == 1