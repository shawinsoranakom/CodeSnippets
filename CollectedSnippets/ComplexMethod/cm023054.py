async def test_ip_bans_file_creation(
    hass: HomeAssistant,
    aiohttp_client: ClientSessionGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Testing if banned IP file created."""
    app = web.Application()
    app[KEY_HASS] = hass

    async def unauth_handler(request):
        """Return a mock web response."""
        raise HTTPUnauthorized

    app.router.add_get("/example", unauth_handler)
    setup_bans(hass, app, 2)
    mock_real_ip(app)("200.201.202.204")

    with patch(
        "homeassistant.components.http.ban.load_yaml_config_file",
        return_value={
            banned_ip: {"banned_at": "2016-11-16T19:20:03"} for banned_ip in BANNED_IPS
        },
    ):
        client = await aiohttp_client(app)

    manager = app[KEY_BAN_MANAGER]
    m_open = mock_open()

    with patch("homeassistant.components.http.ban.open", m_open, create=True):
        resp = await client.get("/example")
        assert resp.status == HTTPStatus.UNAUTHORIZED
        assert len(manager.ip_bans_lookup) == len(BANNED_IPS)
        assert m_open.call_count == 0

        resp = await client.get("/example")
        assert resp.status == HTTPStatus.UNAUTHORIZED
        assert len(manager.ip_bans_lookup) == len(BANNED_IPS) + 1
        m_open.assert_called_once_with(
            hass.config.path(IP_BANS_FILE), "a", encoding="utf8"
        )

        resp = await client.get("/example")
        assert resp.status == HTTPStatus.FORBIDDEN
        assert m_open.call_count == 1

        notifications = async_get_persistent_notifications(hass)
        assert len(notifications) == 2
        assert (
            notifications["http-login"]["message"]
            == "Login attempt or request with invalid authentication from example.com (200.201.202.204). See the log for details."
        )

        assert (
            "Login attempt or request with invalid authentication from example.com (200.201.202.204). Requested URL: '/example'."
            in caplog.text
        )