async def test_basic_auth_with_debug_ui(hass: HomeAssistant, server_dir: Path) -> None:
    """Test BasicAuth session is created when username and password are provided with debug_ui."""
    config = {
        DOMAIN: {
            CONF_DEBUG_UI: True,
            CONF_USERNAME: "test_user",
            CONF_PASSWORD: "test_pass",
        }
    }

    with (
        patch(
            "homeassistant.components.go2rtc.Server",
            autospec=True,
        ) as mock_server_cls,
        patch("homeassistant.components.go2rtc.ClientSession") as mock_session_cls,
        patch("homeassistant.components.go2rtc.is_docker_env", return_value=True),
        patch(
            "homeassistant.components.go2rtc.shutil.which",
            return_value="/usr/bin/go2rtc",
        ),
    ):
        mock_session = AsyncMock()
        mock_session_cls.return_value = mock_session

        # Configure the Server mock instance
        mock_server_instance = AsyncMock()
        mock_server_cls.return_value = mock_server_instance

        assert await async_setup_component(hass, DOMAIN, config)
        await hass.async_block_till_done(wait_background_tasks=True)

        # Verify ClientSession was created with BasicAuth and UnixConnector
        mock_session_cls.assert_called_once()
        call_kwargs = mock_session_cls.call_args[1]
        assert "connector" in call_kwargs
        connector = call_kwargs["connector"]
        assert isinstance(connector, UnixConnector)
        assert connector.path == get_go2rtc_unix_socket_path(server_dir)
        assert "auth" in call_kwargs
        auth = call_kwargs["auth"]
        assert isinstance(auth, BasicAuth)
        assert auth.login == "test_user"
        assert auth.password == "test_pass"

        # Verify Server was called with username and password
        mock_server_cls.assert_called_once()
        call_kwargs = mock_server_cls.call_args[1]
        assert call_kwargs["username"] == "test_user"
        assert call_kwargs["password"] == "test_pass"