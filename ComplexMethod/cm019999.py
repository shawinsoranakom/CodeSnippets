async def test_manual_configuration_update_configuration(
    hass: HomeAssistant,
    aioclient_mock: AiohttpClientMocker,
    config_entry_setup: MockConfigEntry,
) -> None:
    """Test that manual configuration can update existing config entry."""
    aioclient_mock.get(
        pydeconz.utils.URL_DISCOVER,
        json=[],
        headers={"content-type": CONTENT_TYPE_JSON},
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "manual_input"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input={CONF_HOST: "2.3.4.5", CONF_PORT: 80},
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "link"

    aioclient_mock.post(
        "http://2.3.4.5:80/api",
        json=[{"success": {"username": API_KEY}}],
        headers={"content-type": CONTENT_TYPE_JSON},
    )

    aioclient_mock.get(
        f"http://2.3.4.5:80/api/{API_KEY}/config",
        json={"bridgeid": BRIDGE_ID},
        headers={"content-type": CONTENT_TYPE_JSON},
    )

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={}
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "already_configured"
    assert config_entry_setup.data[CONF_HOST] == "2.3.4.5"