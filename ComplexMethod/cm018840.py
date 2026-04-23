async def test_oauth_flow(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
) -> None:
    """Test we get the form."""

    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
    )

    assert result["type"] is FlowResultType.EXTERNAL_STEP

    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": REDIRECT,
        },
    )

    assert result["url"].startswith(AUTHORIZE_URL)
    parsed_url = urlparse(result["url"])
    parsed_query = parse_qs(parsed_url.query)
    assert parsed_query["response_type"][0] == "code"
    assert parsed_query["client_id"][0] == CLIENT_ID
    assert parsed_query["redirect_uri"][0] == REDIRECT
    assert parsed_query["state"][0] == state
    assert parsed_query["code_challenge"][0]

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    response = {
        "refresh_token": "test_refresh_token",
        "access_token": "test_access_token",
        "type": "Bearer",
        "expires_in": 60,
    }

    aioclient_mock.clear_requests()
    aioclient_mock.post(
        TOKEN_URL,
        json=response,
    )

    # Complete OAuth
    result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert result
    assert result["type"] is FlowResultType.CREATE_ENTRY
    assert result["result"].unique_id == UNIQUE_ID
    assert result["data"]["auth_implementation"] == "teslemetry"
    assert result["data"]["token"]["refresh_token"] == response["refresh_token"]
    assert result["data"]["token"]["access_token"] == response["access_token"]
    assert result["data"]["token"]["type"] == response["type"]
    assert result["data"]["token"]["expires_in"] == response["expires_in"]
    assert "expires_at" in result["result"].data["token"]