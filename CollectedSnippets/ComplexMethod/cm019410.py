async def test_form_errors_reconfigure(
    hass: HomeAssistant, mock_login, error, reason
) -> None:
    """Test we handle cannot connect error."""
    mock_login.side_effect = error
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"username": "test-email@test-domain.com", "token": "test-original-token"},
        unique_id="test-email@test-domain.com",
    )
    mock_entry.add_to_hass(hass)

    result = await mock_entry.start_reconfigure_flow(hass)

    with patch(
        "homeassistant.components.melcloud.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PASSWORD: "test-password"},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == reason

    mock_login.side_effect = None
    with patch(
        "homeassistant.components.melcloud.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PASSWORD: "test-password"},
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    entry = hass.config_entries.async_get_entry(mock_entry.entry_id)
    assert entry
    assert entry.title == "Mock Title"
    assert entry.data == {
        "username": "test-email@test-domain.com",
        "token": "test-token",
        "password": "test-password",
    }