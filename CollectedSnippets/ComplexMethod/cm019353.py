async def test_full_flow_application_creds(
    hass: HomeAssistant,
    mock_code_flow: Mock,
    mock_exchange: Mock,
) -> None:
    """Test successful creds setup."""
    await async_import_client_credential(
        hass, DOMAIN, ClientCredential(CLIENT_ID, CLIENT_SECRET), "imported-cred"
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result.get("type") is FlowResultType.SHOW_PROGRESS
    assert result.get("step_id") == "auth"
    assert "description_placeholders" in result
    assert "url" in result["description_placeholders"]

    with patch(
        "homeassistant.components.google.async_setup_entry", return_value=True
    ) as mock_setup:
        # Run one tick to invoke the credential exchange check
        now = utcnow()
        await fire_alarm(hass, now + CODE_CHECK_ALARM_TIMEDELTA)
        await hass.async_block_till_done()
        result = await hass.config_entries.flow.async_configure(
            flow_id=result["flow_id"]
        )

    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == EMAIL_ADDRESS
    assert "data" in result
    data = result["data"]
    assert "token" in data
    assert 0 < data["token"]["expires_in"] < 8 * 86400
    assert (
        datetime.datetime.now().timestamp()
        <= data["token"]["expires_at"]
        < (datetime.datetime.now() + datetime.timedelta(days=8)).timestamp()
    )
    data["token"].pop("expires_at")
    data["token"].pop("expires_in")
    assert data == {
        "auth_implementation": "imported-cred",
        "token": {
            "access_token": "ACCESS_TOKEN",
            "refresh_token": "REFRESH_TOKEN",
            "scope": "https://www.googleapis.com/auth/calendar",
            "token_type": "Bearer",
        },
        "credential_type": "device_auth",
    }
    assert result.get("options") == {"calendar_access": "read_write"}

    assert len(mock_setup.mock_calls) == 1
    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1