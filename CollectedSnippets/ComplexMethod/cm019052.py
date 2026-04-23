async def test_reauth(hass: HomeAssistant, snapshot: SnapshotAssertion) -> None:
    """Test that the re-auth flow works."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title="https://my.nc_url.local",
        unique_id="nc_url",
        data=VALID_CONFIG,
    )
    entry.add_to_hass(hass)

    # start reauth flow
    result = await entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    # test NextcloudMonitorAuthorizationError
    with patch(
        "homeassistant.components.nextcloud.config_flow.NextcloudMonitor",
        side_effect=NextcloudMonitorAuthorizationError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "other_user",
                CONF_PASSWORD: "other_password",
            },
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": "invalid_auth"}

    # test NextcloudMonitorConnectionError
    with patch(
        "homeassistant.components.nextcloud.config_flow.NextcloudMonitor",
        side_effect=NextcloudMonitorConnectionError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "other_user",
                CONF_PASSWORD: "other_password",
            },
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": "connection_error"}

    # test NextcloudMonitorRequestError
    with patch(
        "homeassistant.components.nextcloud.config_flow.NextcloudMonitor",
        side_effect=NextcloudMonitorRequestError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "other_user",
                CONF_PASSWORD: "other_password",
            },
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert result["errors"] == {"base": "connection_error"}

    # test success
    with patch(
        "homeassistant.components.nextcloud.config_flow.NextcloudMonitor",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_USERNAME: "other_user",
                CONF_PASSWORD: "other_password",
            },
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data == snapshot