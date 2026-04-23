async def test_reauth_password_success(
    hass: HomeAssistant,
    mock_growatt_classic_api: MagicMock,
    stored_url: str,
    user_input: dict[str, str],
    expected_region: str,
) -> None:
    """Test successful reauthentication with password auth for default and non-default regions."""
    entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            CONF_AUTH_TYPE: AUTH_PASSWORD,
            CONF_USERNAME: "test_user",
            CONF_PASSWORD: "test_password",
            CONF_URL: stored_url,
            CONF_PLANT_ID: "123456",
            CONF_NAME: "Test Plant",
        },
        unique_id="123456",
    )
    entry.add_to_hass(hass)

    result = await entry.start_reauth_flow(hass)

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"
    region_key = next(
        k
        for k in result["data_schema"].schema
        if isinstance(k, vol.Required) and k.schema == CONF_REGION
    )
    assert region_key.default() == expected_region

    mock_growatt_classic_api.login.return_value = GROWATT_LOGIN_RESPONSE
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input
    )

    assert result["type"] is FlowResultType.ABORT
    assert result["reason"] == "reauth_successful"
    assert entry.data == {
        CONF_AUTH_TYPE: AUTH_PASSWORD,
        CONF_NAME: "Test Plant",
        CONF_PASSWORD: user_input[CONF_PASSWORD],
        CONF_PLANT_ID: "123456",
        CONF_URL: SERVER_URLS_NAMES[user_input[CONF_REGION]],
        CONF_USERNAME: user_input[CONF_USERNAME],
    }