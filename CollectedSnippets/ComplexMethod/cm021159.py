async def test_reauth(
    hass: HomeAssistant,
    freezer: FrozenDateTimeFactory,
    pvpc_aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test reauth flow for API-token mode."""
    freezer.move_to(_MOCK_TIME_BAD_AUTH_RESPONSES)
    await hass.config.async_set_time_zone("Europe/Madrid")
    tst_config = {
        CONF_NAME: "test",
        ATTR_TARIFF: TARIFFS[1],
        ATTR_POWER: 4.6,
        ATTR_POWER_P3: 5.75,
        CONF_USE_API_TOKEN: True,
    }

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], tst_config
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "api_token"
    assert pvpc_aioclient_mock.call_count == 0

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_TOKEN: "test-token"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "api_token"
    assert result["errors"]["base"] == "invalid_auth"
    assert pvpc_aioclient_mock.call_count == 1

    freezer.move_to(_MOCK_TIME_VALID_RESPONSES)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_TOKEN: "test-token"}
    )
    assert result["type"] is FlowResultType.CREATE_ENTRY
    config_entry = result["result"]
    assert pvpc_aioclient_mock.call_count == 4

    # check reauth trigger with bad-auth responses
    freezer.move_to(_MOCK_TIME_BAD_AUTH_RESPONSES)
    async_fire_time_changed(hass, _MOCK_TIME_BAD_AUTH_RESPONSES)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert pvpc_aioclient_mock.call_count == 6

    result = hass.config_entries.flow.async_progress_by_handler(DOMAIN)[0]
    assert result["context"]["entry_id"] == config_entry.entry_id
    assert result["context"]["source"] == config_entries.SOURCE_REAUTH
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_TOKEN: "test-token"}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    assert pvpc_aioclient_mock.call_count == 7

    result = hass.config_entries.flow.async_progress_by_handler(DOMAIN)[0]
    assert result["context"]["entry_id"] == config_entry.entry_id
    assert result["context"]["source"] == config_entries.SOURCE_REAUTH
    assert result["step_id"] == "reauth_confirm"

    freezer.move_to(_MOCK_TIME_VALID_RESPONSES)
    async_fire_time_changed(hass, _MOCK_TIME_VALID_RESPONSES)
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_API_TOKEN: "test-token"}
    )
    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert pvpc_aioclient_mock.call_count == 8

    await hass.async_block_till_done(wait_background_tasks=True)
    assert pvpc_aioclient_mock.call_count == 10