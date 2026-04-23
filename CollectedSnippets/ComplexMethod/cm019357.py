async def test_reauth_flow(
    hass: HomeAssistant,
    mock_code_flow: Mock,
    mock_exchange: Mock,
    options: dict[str, Any] | None,
) -> None:
    """Test reauth of an existing config entry."""
    config_entry = MockConfigEntry(
        domain=DOMAIN,
        data={
            "auth_implementation": DOMAIN,
            "token": {"access_token": "OLD_ACCESS_TOKEN"},
        },
        options=options,
    )
    config_entry.add_to_hass(hass)
    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential(CLIENT_ID, CLIENT_SECRET),
    )

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1

    result = await config_entry.start_reauth_flow(hass)
    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "reauth_confirm"

    result = await hass.config_entries.flow.async_configure(
        flow_id=result["flow_id"],
        user_input={},
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

    assert result.get("type") is FlowResultType.ABORT
    assert result.get("reason") == "reauth_successful"

    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1
    data = entries[0].data
    assert "token" in data
    data["token"].pop("expires_at")
    data["token"].pop("expires_in")
    assert data == {
        "auth_implementation": DOMAIN,
        "token": {
            "access_token": "ACCESS_TOKEN",
            "refresh_token": "REFRESH_TOKEN",
            "scope": "https://www.googleapis.com/auth/calendar",
            "token_type": "Bearer",
        },
        "credential_type": "device_auth",
    }
    # Options are preserved during reauth
    assert entries[0].options == options

    assert len(mock_setup.mock_calls) == 1