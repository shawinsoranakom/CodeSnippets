async def test_form_persists_device_id_on_error(
    hass: HomeAssistant,
    mock_jellyfin: MagicMock,
    mock_client: MagicMock,
    mock_client_device_id: MagicMock,
) -> None:
    """Test persisting the device id on error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] is FlowResultType.FORM
    assert result["errors"] == {}

    mock_client_device_id.return_value = "TEST-UUID-1"
    mock_client.auth.login.return_value = await async_load_json_fixture(
        hass, "auth-login-failure.json"
    )

    result2 = await hass.config_entries.flow.async_configure(
        result["flow_id"],
        user_input=USER_INPUT,
    )
    await hass.async_block_till_done()

    assert result2["type"] is FlowResultType.FORM
    assert result2["errors"] == {"base": "invalid_auth"}

    mock_client_device_id.return_value = "TEST-UUID-2"
    mock_client.auth.login.return_value = await async_load_json_fixture(
        hass, "auth-login.json"
    )

    result3 = await hass.config_entries.flow.async_configure(
        result2["flow_id"],
        user_input=USER_INPUT,
    )
    await hass.async_block_till_done()

    assert result3
    assert result3["type"] is FlowResultType.CREATE_ENTRY
    assert result3["data"] == {
        CONF_CLIENT_DEVICE_ID: "TEST-UUID-1",
        CONF_URL: TEST_URL,
        CONF_USERNAME: TEST_USERNAME,
        CONF_PASSWORD: TEST_PASSWORD,
    }