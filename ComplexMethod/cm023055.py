async def test_failed_login_attempts_counter(
    hass: HomeAssistant, aiohttp_client: ClientSessionGenerator
) -> None:
    """Testing if failed login attempts counter increased."""
    app = web.Application()
    app[KEY_HASS] = hass

    async def auth_handler(request):
        """Return 200 status code."""
        return None, 200

    async def auth_true_handler(request):
        """Return 200 status code."""
        process_success_login(request)
        return None, 200

    app.router.add_get(
        "/auth_true",
        request_handler_factory(hass, Mock(requires_auth=True), auth_true_handler),
    )
    app.router.add_get(
        "/auth_false",
        request_handler_factory(hass, Mock(requires_auth=True), auth_handler),
    )
    app.router.add_get(
        "/", request_handler_factory(hass, Mock(requires_auth=False), auth_handler)
    )

    setup_bans(hass, app, 5)
    remote_ip = ip_address("200.201.202.204")
    mock_real_ip(app)("200.201.202.204")

    @middleware
    async def mock_auth(request, handler):
        """Mock auth middleware."""
        if "auth_true" in request.path:
            request[KEY_AUTHENTICATED] = True
        else:
            request[KEY_AUTHENTICATED] = False
        return await handler(request)

    app.middlewares.append(mock_auth)

    client = await aiohttp_client(app)

    resp = await client.get("/auth_false")
    assert resp.status == HTTPStatus.UNAUTHORIZED
    assert app[KEY_FAILED_LOGIN_ATTEMPTS][remote_ip] == 1

    resp = await client.get("/auth_false")
    assert resp.status == HTTPStatus.UNAUTHORIZED
    assert app[KEY_FAILED_LOGIN_ATTEMPTS][remote_ip] == 2

    resp = await client.get("/")
    assert resp.status == HTTPStatus.OK
    assert app[KEY_FAILED_LOGIN_ATTEMPTS][remote_ip] == 2

    # This used to check that with trusted networks we reset login attempts
    # We no longer support trusted networks.
    resp = await client.get("/auth_true")
    assert resp.status == HTTPStatus.OK
    assert app[KEY_FAILED_LOGIN_ATTEMPTS][remote_ip] == 0

    resp = await client.get("/auth_false")
    assert resp.status == HTTPStatus.UNAUTHORIZED
    assert app[KEY_FAILED_LOGIN_ATTEMPTS][remote_ip] == 1

    resp = await client.get("/auth_false")
    assert resp.status == HTTPStatus.UNAUTHORIZED
    assert app[KEY_FAILED_LOGIN_ATTEMPTS][remote_ip] == 2