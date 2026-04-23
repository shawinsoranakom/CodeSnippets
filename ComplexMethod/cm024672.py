async def test_full_flow(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    mock_setup: Mock,
) -> None:
    """Check full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    state = config_entry_oauth2_flow._encode_jwt(
        hass,
        {
            "flow_id": result["flow_id"],
            "redirect_uri": "https://example.com/auth/external/callback",
        },
    )

    assert result["url"] == (
        f"{OAUTH2_AUTHORIZE}?response_type=code&client_id={CLIENT_ID}"
        "&redirect_uri=https://example.com/auth/external/callback"
        f"&state={state}"
        "&scope=https://www.googleapis.com/auth/photoslibrary.readonly.appcreateddata"
        "+https://www.googleapis.com/auth/photoslibrary.appendonly"
        "+https://www.googleapis.com/auth/userinfo.profile"
        "&access_type=offline&prompt=consent"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    result = await hass.config_entries.flow.async_configure(result["flow_id"])
    assert result["type"] is FlowResultType.CREATE_ENTRY
    config_entry = result["result"]
    assert config_entry.unique_id == USER_IDENTIFIER
    assert config_entry.title == "Test Name"
    config_entry_data = dict(config_entry.data)
    assert "token" in config_entry_data
    assert "expires_at" in config_entry_data["token"]
    del config_entry_data["token"]["expires_at"]
    assert config_entry_data == {
        "auth_implementation": DOMAIN,
        "token": {
            "access_token": FAKE_ACCESS_TOKEN,
            "expires_in": EXPIRES_IN,
            "refresh_token": FAKE_REFRESH_TOKEN,
            "type": "Bearer",
            "scope": (
                "https://www.googleapis.com/auth/photoslibrary.readonly.appcreateddata"
                " https://www.googleapis.com/auth/photoslibrary.appendonly"
                " https://www.googleapis.com/auth/userinfo.profile"
            ),
        },
    }
    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert len(mock_setup.mock_calls) == 1