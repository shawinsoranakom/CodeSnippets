async def test_ingress_request_get(
    hassio_noauth_client, build_type, aioclient_mock: AiohttpClientMocker
) -> None:
    """Test no auth needed for ."""
    aioclient_mock.get(
        f"http://127.0.0.1/ingress/{build_type[0]}/{build_type[1]}",
        text="test",
        headers=CIMultiDict(
            [("Set-Cookie", "cookie1=value1"), ("Set-Cookie", "cookie2=value2")]
        ),
    )

    resp = await hassio_noauth_client.get(
        f"/api/hassio_ingress/{build_type[0]}/{build_type[1]}",
        headers=CIMultiDict(
            [("X-Test-Header", "beer"), ("X-Test-Header", "more beer")]
        ),
    )

    # Check we got right response
    assert resp.status == HTTPStatus.OK
    assert resp.headers["Set-Cookie"] == "cookie1=value1"
    assert resp.headers.getall("Set-Cookie") == ["cookie1=value1", "cookie2=value2"]
    body = await resp.text()
    assert body == "test"

    # Check we forwarded command
    assert len(aioclient_mock.mock_calls) == 1
    assert X_AUTH_TOKEN not in aioclient_mock.mock_calls[-1][3]
    assert aioclient_mock.mock_calls[-1][3]["X-Hass-Source"] == "core.ingress"
    assert (
        aioclient_mock.mock_calls[-1][3]["X-Ingress-Path"]
        == f"/api/hassio_ingress/{build_type[0]}"
    )
    assert aioclient_mock.mock_calls[-1][3]["X-Test-Header"] == "beer"
    assert aioclient_mock.mock_calls[-1][3].getall("X-Test-Header") == [
        "beer",
        "more beer",
    ]
    assert aioclient_mock.mock_calls[-1][3][X_FORWARDED_FOR]
    assert aioclient_mock.mock_calls[-1][3][X_FORWARDED_HOST]
    assert aioclient_mock.mock_calls[-1][3][X_FORWARDED_PROTO]