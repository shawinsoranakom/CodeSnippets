async def test_cloud_errors(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_lametric_cloud: MagicMock,
    mock_lametric: MagicMock,
    side_effect: Exception,
    reason: str,
) -> None:
    """Test adding existing device updates existing entry."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"next_step_id": "pick_implementation"}
    )

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )
    client = await hass_client_no_auth()
    await client.get(f"/auth/external/callback?code=abcd&state={state}")
    aioclient_mock.post(
        "https://developer.lametric.com/api/v2/oauth2/token",
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )
    await hass.config_entries.flow.async_configure(result["flow_id"])

    mock_lametric.device.side_effect = side_effect
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_DEVICE: "SA110405124500W00BS9"}
    )

    assert result["type"] is FlowResultType.FORM
    assert result["step_id"] == "cloud_select_device"
    assert result["errors"] == {"base": reason}

    assert len(mock_lametric_cloud.devices.mock_calls) == 1
    assert len(mock_lametric.device.mock_calls) == 1
    assert len(mock_lametric.notify.mock_calls) == 0

    mock_lametric.device.side_effect = None
    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={CONF_DEVICE: "SA110405124500W00BS9"}
    )

    assert result["type"] is FlowResultType.CREATE_ENTRY

    config_entry = result["result"]
    assert config_entry.title == "Frenck's LaMetric"
    assert config_entry.unique_id == "SA110405124500W00BS9"
    assert config_entry.data == {
        CONF_HOST: "127.0.0.1",
        CONF_API_KEY: "mock-api-key",
        CONF_MAC: "AA:BB:CC:DD:EE:FF",
    }
    assert not config_entry.options

    assert len(mock_lametric_cloud.devices.mock_calls) == 1
    assert len(mock_lametric.device.mock_calls) == 2
    assert len(mock_lametric.notify.mock_calls) == 1