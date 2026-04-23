async def test_cors_requests(client) -> None:
    """Test cross origin requests."""
    req = await client.get("/", headers={ORIGIN: TRUSTED_ORIGIN})
    assert req.status == HTTPStatus.OK
    assert req.headers[ACCESS_CONTROL_ALLOW_ORIGIN] == TRUSTED_ORIGIN

    # With password in URL
    req = await client.get(
        "/", params={"api_password": "some-pass"}, headers={ORIGIN: TRUSTED_ORIGIN}
    )
    assert req.status == HTTPStatus.OK
    assert req.headers[ACCESS_CONTROL_ALLOW_ORIGIN] == TRUSTED_ORIGIN

    # With password in headers
    req = await client.get(
        "/", headers={HTTP_HEADER_HA_AUTH: "some-pass", ORIGIN: TRUSTED_ORIGIN}
    )
    assert req.status == HTTPStatus.OK
    assert req.headers[ACCESS_CONTROL_ALLOW_ORIGIN] == TRUSTED_ORIGIN

    # With auth token in headers
    req = await client.get(
        "/", headers={AUTHORIZATION: "Bearer some-token", ORIGIN: TRUSTED_ORIGIN}
    )
    assert req.status == HTTPStatus.OK
    assert req.headers[ACCESS_CONTROL_ALLOW_ORIGIN] == TRUSTED_ORIGIN