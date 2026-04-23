async def test_full_flow(
    hass: HomeAssistant,
    hass_client_no_auth: ClientSessionGenerator,
    aioclient_mock: AiohttpClientMocker,
    mock_api: MagicMock,
    snapshot: SnapshotAssertion,
) -> None:
    """Check full flow."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": SOURCE_USER}
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
        f"&state={state}&scope=https://www.googleapis.com/auth/drive.file"
        "&access_type=offline&prompt=consent"
    )

    client = await hass_client_no_auth()
    resp = await client.get(f"/auth/external/callback?code=abcd&state={state}")
    assert resp.status == 200
    assert resp.headers["content-type"] == "text/html; charset=utf-8"

    # Prepare API responses
    mock_api.get_user = AsyncMock(
        return_value={"user": {"emailAddress": TEST_USER_EMAIL}}
    )
    mock_api.list_files = AsyncMock(return_value={"files": []})
    mock_api.create_file = AsyncMock(
        return_value={"id": FOLDER_ID, "name": FOLDER_NAME}
    )

    aioclient_mock.post(
        GOOGLE_TOKEN_URI,
        json={
            "refresh_token": "mock-refresh-token",
            "access_token": "mock-access-token",
            "type": "Bearer",
            "expires_in": 60,
        },
    )

    with patch(
        "homeassistant.components.google_drive.async_setup_entry", return_value=True
    ) as mock_setup:
        result = await hass.config_entries.flow.async_configure(result["flow_id"])

    assert len(hass.config_entries.async_entries(DOMAIN)) == 1
    assert len(mock_setup.mock_calls) == 1
    assert len(aioclient_mock.mock_calls) == 1
    assert [tuple(mock_call) for mock_call in mock_api.mock_calls] == snapshot

    assert result.get("type") is FlowResultType.CREATE_ENTRY
    assert result.get("title") == TITLE
    assert result.get("description_placeholders") == {
        "folder_name": FOLDER_NAME,
        "url": f"https://drive.google.com/drive/folders/{FOLDER_ID}",
    }
    assert "result" in result
    assert result.get("result").unique_id == TEST_USER_EMAIL
    assert "token" in result.get("result").data
    assert result.get("result").data["token"].get("access_token") == "mock-access-token"
    assert (
        result.get("result").data["token"].get("refresh_token") == "mock-refresh-token"
    )