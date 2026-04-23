async def test_user_create_entry(
    hass: HomeAssistant, snapshot: SnapshotAssertion
) -> None:
    """Test that the user step works."""
    # start user flow
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {}

    # test NextcloudMonitorAuthorizationError
    with patch(
        "homeassistant.components.nextcloud.config_flow.NextcloudMonitor",
        side_effect=NextcloudMonitorAuthorizationError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_auth"}

    # test NextcloudMonitorConnectionError
    with patch(
        "homeassistant.components.nextcloud.config_flow.NextcloudMonitor",
        side_effect=NextcloudMonitorConnectionError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "connection_error"}

    # test NextcloudMonitorRequestError
    with patch(
        "homeassistant.components.nextcloud.config_flow.NextcloudMonitor",
        side_effect=NextcloudMonitorRequestError,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "connection_error"}

    # test success
    with patch(
        "homeassistant.components.nextcloud.config_flow.NextcloudMonitor",
        return_value=True,
    ):
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            VALID_CONFIG,
        )
        await hass.async_block_till_done()

    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["title"] == "https://my.nc_url.local"
    assert result["data"] == snapshot