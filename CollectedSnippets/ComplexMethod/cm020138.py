async def test_ingress_websocket(
    hassio_noauth_client, build_type, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test no auth needed for ."""
    aioclient_mock.get(f"http://127.0.0.1/ingress/{build_type[0]}/{build_type[1]}")

    # Ignore error because we can setup a full IO infrastructure
    await hassio_noauth_client.ws_connect(
        f"/api/hassio_ingress/{build_type[0]}/{build_type[1]}",
        headers={"X-Test-Header": "beer"},
    )

    # Check we forwarded command
    assert len(aioclient_mock.mock_calls) == 1
    assert X_AUTH_TOKEN not in aioclient_mock.mock_calls[-1][3]
    assert aioclient_mock.mock_calls[-1][3]["X-Hass-Source"] == "core.ingress"
    assert (
        aioclient_mock.mock_calls[-1][3]["X-Ingress-Path"]
        == f"/api/hassio_ingress/{build_type[0]}"
    )
    assert aioclient_mock.mock_calls[-1][3]["X-Test-Header"] == "beer"
    assert aioclient_mock.mock_calls[-1][3][X_FORWARDED_FOR]
    assert aioclient_mock.mock_calls[-1][3][X_FORWARDED_HOST]
    assert aioclient_mock.mock_calls[-1][3][X_FORWARDED_PROTO]