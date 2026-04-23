async def test_flow_user(hass: HomeAssistant, mock_api: requests_mock.Mocker) -> None:
    """Test the user flow."""
    # Open flow as USER with no input
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={CONF_SOURCE: SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"

    # Test flow with connection failure, fail with cannot_connect
    with requests_mock.Mocker() as mock:
        mock.get(
            f"{USER_INPUT[CONF_URL]}/api/v2/app/preferences",
            exc=RequestException,
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "cannot_connect"}

    # Test flow with wrong creds, fail with invalid_auth
    with requests_mock.Mocker() as mock:
        mock.head(USER_INPUT[CONF_URL])
        mock.post(
            f"{USER_INPUT[CONF_URL]}/api/v2/auth/login",
            text="Wrong username/password",
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "user"
    assert result["errors"] == {"base": "invalid_auth"}

    # Test flow with proper input, succeed
    with requests_mock.Mocker() as mock:
        mock.head(USER_INPUT[CONF_URL])
        mock.post(
            f"{USER_INPUT[CONF_URL]}/api/v2/auth/login",
            text="Ok.",
        )
        result = await hass.config_entries.flow.async_configure(
            result["flow_id"], USER_INPUT
        )
        await hass.async_block_till_done()
    assert result["type"] is FlowResultType.CREATE_ENTRY

    assert result["data"] == {
        CONF_URL: "http://localhost:8080",
        CONF_USERNAME: "user",
        CONF_PASSWORD: "pass",
        CONF_VERIFY_SSL: True,
    }