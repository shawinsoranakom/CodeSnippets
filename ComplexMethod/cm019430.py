async def _test_websocket_webrtc_offer_webrtc_provider(
    hass: HomeAssistant,
    hass_ws_client: WebSocketGenerator,
    register_test_provider: SomeTestProvider,
    message: WebRTCMessage,
    expected_frontend_message: dict[str, Any],
) -> None:
    """Test initiating a WebRTC stream with a webrtc provider."""
    client = await hass_ws_client(hass)
    with (
        patch.object(
            register_test_provider, "async_handle_async_webrtc_offer", autospec=True
        ) as mock_async_handle_async_webrtc_offer,
        patch.object(
            register_test_provider, "async_close_session", autospec=True
        ) as mock_async_close_session,
    ):
        await client.send_json_auto_id(
            {
                "type": "camera/webrtc/offer",
                "entity_id": "camera.demo_camera",
                "offer": WEBRTC_OFFER,
            }
        )
        response = await client.receive_json()
        assert response["type"] == TYPE_RESULT
        assert response["success"]
        subscription_id = response["id"]
        mock_async_handle_async_webrtc_offer.assert_called_once()
        assert mock_async_handle_async_webrtc_offer.call_args[0][1] == WEBRTC_OFFER
        send_message: WebRTCSendMessage = (
            mock_async_handle_async_webrtc_offer.call_args[0][3]
        )

        # Session id
        response = await client.receive_json()
        assert response["id"] == subscription_id
        assert response["type"] == "event"
        assert response["event"]["type"] == "session"
        session_id = response["event"]["session_id"]

        send_message(message)

        response = await client.receive_json()
        assert response["id"] == subscription_id
        assert response["type"] == "event"
        assert response["event"] == expected_frontend_message

        # Unsubscribe/Close session
        await client.send_json_auto_id(
            {
                "type": "unsubscribe_events",
                "subscription": subscription_id,
            }
        )
        msg = await client.receive_json()
        assert msg["success"]
        mock_async_close_session.assert_called_once_with(session_id)