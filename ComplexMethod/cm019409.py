async def test_reconfigure_flow(
    hass: HomeAssistant, mock_login, mock_request_info, error, reason
) -> None:
    """Test re-configuration flow."""
    mock_login.side_effect = ClientResponseError(mock_request_info(), (), status=error)
    mock_entry = MockConfigEntry(
        domain=DOMAIN,
        data={"username": "test-email@test-domain.com", "token": "test-original-token"},
        unique_id="test-email@test-domain.com",
    )
    mock_entry.add_to_hass(hass)

    result = await mock_entry.start_reconfigure_flow(hass)

    assert result["type"] is FlowResultType.FORM

    with patch(
        "homeassistant.components.melcloud.async_setup_entry",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {CONF_PASSWORD: "test-password"},
        )
        await hass.async_block_till_done()

    assert result["errors"]["base"] == reason
    assert result["type"] is FlowResultType.FORM

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