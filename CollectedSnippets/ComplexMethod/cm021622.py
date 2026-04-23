async def test_full_ssdp_with_cloud_import(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_lametric_cloud: MagicMock,
    mock_lametric: MagicMock,
) -> None:
    """Check a full flow triggered by SSDP, importing from cloud."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_SSDP}, data=SSDP_DISCOVERY_INFO
    )

    assert result["type"] is FlowResultType.MENU
    assert result["step_id"] == "choice_enter_manual_or_fetch_cloud"
    assert result["menu_options"] == ["pick_implementation", "manual_entry"]

    result = await hass.config_entries.flow.async_configure(
        result["flow_id"], user_input={"next_step_id": "pick_implementation"}
    )

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    assert result["type"] is FlowResultType.EXTERNAL_STEP
    assert result["url"] == (
        "https://developer.lametric.com/api/v2/oauth2/authorize"
        "?response_type=code&client_id=client"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}"
        "&scope=basic+devices_read"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == HTTPStatus.OK
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    aioclient_mock.post(
        "https://developer.lametric.com/api/v2/oauth2/token",
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result["type"] is FlowResultType.CREATE_ENTRY

    config_entry = result["result"]
    assert config_entry.title == "Frenck's LaMetric"
    assert config_entry.unique_id == "SA110405124500W00BS9"
    assert config_entry.data == {
        CONF_HOST: "127.0.0.1",
        CONF_API_KEY: "mock-api-key",
        CONF_MAC: "AA:BB:CC:DD:EE:FF",
    }

    assert len(mock_lametric_cloud.devices.mock_calls) == 1
    assert len(mock_lametric.device.mock_calls) == 1
    assert len(mock_lametric.notify.mock_calls) == 1