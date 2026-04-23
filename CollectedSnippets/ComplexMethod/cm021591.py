async def config_flow(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
) -> config_entries.ConfigFlowResult:
    """Initialize a new config flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": REDIRECT_URI,
        },
    )

    result_url = URL(result["url"])
    assert f"{result_url.origin()}{result_url.path}" == AUTHORIZE_URL
    assert result_url.query["response_type"] == "code"
    assert result_url.query["client_id"] == CLIENT_ID
    assert result_url.query["redirect_uri"] == REDIRECT_URI
    assert result_url.query["state"] == state
    assert result_url.query["code_challenge"]
    assert result_url.query["code_challenge_method"] == "S256"
    assert result_url.query["scope"] == " ".join(ALL_SCOPES)

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    return result