async def test_full_flow(
    hass: HomeAssistant, hass_client_no_auth: ClientSessionGenerator
) -> None:
    """Check full flow."""
    result = await hass.config_entries.flow.async_init(
        "google_mail", context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    assert result["url"] == (
        f"{GOOGLE_AUTH_URI}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}&scope={'+'.join(SCOPES)}"
        "&access_type=offline&prompt=consent"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    with (
        patch(
            "homeassistant.components.google_mail.async_setup_entry", return_value=True
        ) as mock_setup,
        patch(
            "httplib2.Http.request",
            return_value=(
                Response({}),
                bytes(
                    await async_load_fixture(hass, "get_profile.json", DOMAIN),
                    encoding="UTF-8",
                ),
            ),
        ),
    ):
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert len(mock_setup.mock_calls) == 1

    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == TITLE
    assert "result" in result
    assert result.get("result").unique_id == TITLE
    assert "token" in result.get("result").data
    assert result.get("result").data["token"].get("access_token") == "mock-access-token"
    assert (
        result.get("result").data["token"].get("refresh_token") == "mock-refresh-token"
    )