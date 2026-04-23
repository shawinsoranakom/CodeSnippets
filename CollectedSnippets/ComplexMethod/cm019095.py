async def test_unix_socket_connection(hass: HomeAssistant, server_dir: Path) -> None:
    """Test Unix socket is used for HA-managed go2rtc instances."""
    config = {DOMAIN: {}}

    with (
        patch("homeassistant.components.go2rtc.ClientSession") as mock_session_cls,
        patch("homeassistant.components.go2rtc.token_hex") as mock_token_hex,
    ):
        mock_session = AsyncMock()
        mock_session_cls.return_value = mock_session
        # First call for username, second call for password
        mock_token_hex.side_effect = ["mock_username_token", "mock_password_token"]

        assert await async_setup_component(hass, DOMAIN, config)
        await hass.async_block_till_done(wait_background_tasks=True)

        # Verify ClientSession was created with UnixConnector and auth
        mock_session_cls.assert_called_once()
        call_kwargs = mock_session_cls.call_args[1]
        assert "connector" in call_kwargs
        connector = call_kwargs["connector"]
        assert isinstance(connector, UnixConnector)
        assert connector.path == get_go2rtc_unix_socket_path(server_dir)
        # Auth should be auto-generated when credentials are not explicitly configured
        assert "auth" in call_kwargs
        auth = call_kwargs["auth"]
        assert isinstance(auth, BasicAuth)
        # Verify auto-generated credentials match our mocked values
        assert auth.login == "mock_username_token"
        assert auth.password == "mock_password_token"

        hass.bus.async_fire(EVENT_HOMEASSISTANT_STOP)
        await hass.async_block_till_done()

        mock_session.close.assert_called_once()