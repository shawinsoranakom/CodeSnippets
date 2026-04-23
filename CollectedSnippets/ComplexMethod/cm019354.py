async def test_exchange_error(
    hass: HomeAssistant,
    mock_code_flow: Mock,
    mock_exchange: Mock,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test an error while exchanging the code for credentials."""
    await async_import_client_credential(
        hass,
        DOMAIN,
        ClientCredential(CLIENT_ID, CLIENT_SECRET),
    )

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result.get("type") is FlowResultType.SHOW_PROGRESS
    assert result.get("step_id") == "auth"
    assert "description_placeholders" in result
    assert "url" in result["description_placeholders"]

    # Run one tick to invoke the credential exchange check
    step2_exchange_called = asyncio.Event()

    def step2_exchange(*args, **kwargs):
        hass.loop.call_soon_threadsafe(step2_exchange_called.set)
        raise FlowExchangeError

    with patch(
        "homeassistant.components.google.api.OAuth2WebServerFlow.step2_exchange",
        side_effect=step2_exchange,
    ):
        freezer.tick(CODE_CHECK_ALARM_TIMEDELTA)
        async_fire_time_changed(hass, utcnow())
        await step2_exchange_called.wait()

    # Status has not updated, will retry
    result = await hass.config_entries.flow.async_configure(flow_id=result["flow_id"])
    assert result.get("type") is FlowResultType.SHOW_PROGRESS
    assert result.get("step_id") == "auth"

    # Run another tick, which attempts credential exchange again
    with patch(
        "homeassistant.components.google.async_setup_entry", return_value=True
    ) as mock_setup:
        freezer.tick(CODE_CHECK_ALARM_TIMEDELTA)
        async_fire_time_changed(hass, utcnow())
        await hass.async_block_till_done()
        result = await hass.config_entries.flow.async_configure(
            flow_id=result["flow_id"]
        )

    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == EMAIL_ADDRESS
    assert "data" in result
    data = result["data"]
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

    assert len(mock_setup.mock_calls) == 1
    entries = hass.config_entries.async_entries(DOMAIN)
    assert len(entries) == 1