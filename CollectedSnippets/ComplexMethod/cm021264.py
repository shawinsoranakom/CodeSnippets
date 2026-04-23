async def test_ws_delete_all_refresh_tokens_error(
    hass: HomeAssistant,
    hass_admin_user: MockUser,
    hass_admin_credential: Credentials,
    hass_ws_client: WebSocketGenerator,
    hass_access_token: str,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test deleting all refresh tokens, where a revoke callback raises an error."""
    assert await async_setup_component(hass, "auth", {"http": {}})

    # one token already exists
    await hass.auth.async_create_refresh_token(
        hass_admin_user, CLIENT_ID, credential=hass_admin_credential
    )
    token = await hass.auth.async_create_refresh_token(
        hass_admin_user, CLIENT_ID + "_1", credential=hass_admin_credential
    )

    def cb():
        raise RuntimeError("I'm bad")

    hass.auth.async_register_revoke_token_callback(token.id, cb)

    ws_client = await hass_ws_client(hass, hass_access_token)

    # get all tokens
    await ws_client.send_json({"id": 5, "type": "auth/refresh_tokens"})
    result = await ws_client.receive_json()
    assert result["success"], result

    tokens = result["result"]

    with patch("homeassistant.components.auth.DELETE_CURRENT_TOKEN_DELAY", 0.001):
        await ws_client.send_json(
            {
                "id": 6,
                "type": "auth/delete_all_refresh_tokens",
            }
        )

        caplog.clear()
        result = await ws_client.receive_json()
        assert result, result["success"] is False
        assert result["error"] == {
            "code": "token_removing_error",
            "message": "During removal, an error was raised.",
        }

    records = [
        record
        for record in caplog.records
        if record.msg == "Error during refresh token removal"
    ]
    assert len(records) == 1
    assert records[0].levelno == logging.ERROR
    assert records[0].exc_info and str(records[0].exc_info[1]) == "I'm bad"
    assert records[0].name == "homeassistant.components.auth"

    await hass.async_block_till_done()
    for token in tokens:
        refresh_token = hass.auth.async_get_refresh_token(token["id"])
        assert refresh_token is None