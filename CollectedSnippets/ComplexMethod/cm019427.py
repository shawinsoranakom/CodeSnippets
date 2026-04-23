async def test_reconfigure_flow_web_login_and_errors(
    recorder_mock: Recorder,
    hass: HomeAssistant,
    solaredge_web_api: AsyncMock,
    mock_setup_entry: AsyncMock,
) -> None:
    """Test reconfigure flow with web login and error handling."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        title=NAME,
        data={CONF_SITE_ID: SITE_ID, CONF_API_KEY: "old_api_key"},
    )
    entry.add_to_hass(hass)

    result = await entry.start_reconfigure_flow(hass)
    assert result.get("type") is FlowResultType.FORM
    assert result.get("step_id") == "reconfigure"

    # Test error
    solaredge_web_api.async_get_equipment.side_effect = ClientResponseError(
        None, None, status=401
    )
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_SECTION_WEB_AUTH: {
                CONF_USERNAME: USERNAME,
                CONF_PASSWORD: PASSWORD,
            },
        },
    )
    assert result.get("type") is FlowResultType.FORM
    assert result.get("errors") == {"base": "invalid_auth"}

    # Test recovery
    solaredge_web_api.async_get_equipment.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        {
            CONF_SECTION_WEB_AUTH: {
                CONF_USERNAME: USERNAME,
                CONF_PASSWORD: PASSWORD,
            },
        },
    )

    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == "reconfigure_successful"

    await hass.async_block_till_done()

    assert entry.title == NAME
    assert entry.data == {
        CONF_SITE_ID: SITE_ID,
        CONF_USERNAME: USERNAME,
        CONF_PASSWORD: PASSWORD,
    }
    assert mock_setup_entry.call_count == 1