async def test_auth_timeout_logs_at_debug(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test auth timeout is logged at debug level not warning."""
    # Setup websocket API
    assert await async_setup_component(hass, "websocket_api", {})

    client = await hass_client()

    # Patch the auth timeout to be very short (0.001 seconds)
    with (
        caplog.at_level(logging.DEBUG, "homeassistant.components.websocket_api"),
        patch(
            "homeassistant.components.websocket_api.http.AUTH_MESSAGE_TIMEOUT", 0.001
        ),
    ):
        # Try to connect - will timeout quickly since we don't send auth
        ws = await client.ws_connect("/api/websocket")
        # Wait a bit for the timeout to trigger and cleanup to complete
        await asyncio.sleep(0.1)
        await ws.close()
        await asyncio.sleep(0.1)

        # Check that "Did not receive auth message" is logged at debug, not warning
        debug_messages = [
            r.message for r in caplog.records if r.levelno == logging.DEBUG
        ]
        assert any(
            "Disconnected during auth phase: Did not receive auth message" in msg
            for msg in debug_messages
        )

        # Check it's NOT logged at warning level
        warning_messages = [
            r.message for r in caplog.records if r.levelno >= logging.WARNING
        ]
        for msg in warning_messages:
            assert "Did not receive auth message" not in msg