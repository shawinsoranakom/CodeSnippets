async def test_reconfigure_flow_webhooks(
    hass: HomeAssistant,
    mock_broadcast_config_entry: MockConfigEntry,
    mock_external_calls: None,
) -> None:
    """Test reconfigure flow for webhook."""
    mock_broadcast_config_entry.add_to_hass(hass)

    result = await mock_broadcast_config_entry.start_reconfigure_flow(hass)
    assert result["step_id"] == "reconfigure"
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_PLATFORM: PLATFORM_WEBHOOKS,
            SECTION_ADVANCED_SETTINGS: {
                CONF_API_ENDPOINT: DEFAULT_API_ENDPOINT,
                CONF_PROXY_URL: "https://test",
            },
        },
    )
    await hass.async_block_till_done()

    assert result["step_id"] == "webhooks"
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] is None

    # test: invalid url

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_URL: "http://test",
            CONF_TRUSTED_NETWORKS: "149.154.160.0/20,91.108.4.0/22",
        },
    )

    assert result["step_id"] == "webhooks"
    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_url"

    # test: HA external url not configured

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {CONF_TRUSTED_NETWORKS: "149.154.160.0/20,91.108.4.0/22"},
    )

    assert result["step_id"] == "webhooks"
    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "no_url_available"

    # test: invalid trusted networks

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_URL: "https://reconfigure",
            CONF_TRUSTED_NETWORKS: "invalid trusted networks",
        },
    )

    assert result["step_id"] == "webhooks"
    assert result["type"] is FlowResultType.FORM
    assert result["errors"]["base"] == "invalid_trusted_networks"

    # test: valid input

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_URL: "https://reconfigure",
            CONF_TRUSTED_NETWORKS: "149.154.160.0/20",
        },
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reconfigure_successful"
    assert mock_broadcast_config_entry.data[CONF_URL] == "https://reconfigure"
    assert mock_broadcast_config_entry.data[CONF_API_ENDPOINT] == DEFAULT_API_ENDPOINT
    assert mock_broadcast_config_entry.data[CONF_TRUSTED_NETWORKS] == [
        "149.154.160.0/20"
    ]