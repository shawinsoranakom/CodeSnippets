async def test_reconfigure_flow(
    hass: HomeAssistant,
    mock_mastodon_client: AsyncMock,
    mock_setup_entry: AsyncMock,
    mock_config_entry: MockConfigEntry,
) -> None:
    """Test reconfigure flow."""
    mock_config_entry.add_to_hass(hass)

    result = await mock_config_entry.start_reconfigure_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reconfigure"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_CLIENT_ID: "client_id2",
            CONF_CLIENT_SECRET: "client_secret2",
            CONF_ACCESS_TOKEN: "access_token2",
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_config_entry.data[CONF_BASE_URL] == "https://mastodon.social"
    assert mock_config_entry.data[CONF_CLIENT_ID] == "client_id2"
    assert mock_config_entry.data[CONF_CLIENT_SECRET] == "client_secret2"
    assert mock_config_entry.data[CONF_ACCESS_TOKEN] == "access_token2"