async def test_camera_webrtc(
    hass: HomeAssistant,
    mock_ring_client: Mock,
    mock_config_entry: MockConfigEntry,
    entity_registry: er.EntityRegistry,
    mock_ring_devices,
    hass_ws_client: WebSocketGenerator,
    caplog: pytest.LogCaptureFixture,
) -> None:
    """Test WebRTC interactions."""
    caplog.set_level(logging.ERROR)
    await setup_platform(hass, Platform.CAMERA)
    client = await hass_ws_client(hass)

    # sdp offer
    await client.send_json_auto_id(
        {
            "type": "camera/webrtc/offer",
            "entity_id": "camera.front_live_view",
            "offer": "v=0\r\n",
        }
    )
    response = await client.receive_json()
    assert response
    assert response.get("success") is True
    subscription_id = response["id"]
    assert not caplog.text

    front_camera_mock = mock_ring_devices.get_device(FRONT_DEVICE_ID)
    front_camera_mock.generate_async_webrtc_stream.assert_called_once()
    args = front_camera_mock.generate_async_webrtc_stream.call_args.args
    session_id = args[1]
    on_message = args[2]

    # receive session
    response = await client.receive_json()
    event = response.get("event")
    assert event
    assert event.get("type") == "session"
    assert not caplog.text

    # Ring candidate
    on_message(RingWebRtcMessage(candidate="candidate", sdp_m_line_index=1))
    response = await client.receive_json()
    event = response.get("event")
    assert event
    assert event.get("type") == "candidate"
    assert not caplog.text

    # Error message
    on_message(RingWebRtcMessage(error_code=1, error_message="error"))
    response = await client.receive_json()
    event = response.get("event")
    assert event
    assert event.get("type") == "error"
    assert not caplog.text

    # frontend candidate
    await client.send_json_auto_id(
        {
            "type": "camera/webrtc/candidate",
            "entity_id": "camera.front_live_view",
            "session_id": session_id,
            "candidate": {"candidate": "candidate", "sdpMLineIndex": 1},
        }
    )
    response = await client.receive_json()
    assert response
    assert response.get("success") is True
    assert not caplog.text
    front_camera_mock.on_webrtc_candidate.assert_called_once()

    # Invalid frontend candidate
    await client.send_json_auto_id(
        {
            "type": "camera/webrtc/candidate",
            "entity_id": "camera.front_live_view",
            "session_id": session_id,
            "candidate": {"candidate": "candidate", "sdpMid": "1"},
        }
    )
    response = await client.receive_json()
    assert response
    assert response.get("success") is False
    assert response["error"]["code"] == "home_assistant_error"
    error_msg = f"Error negotiating stream for {front_camera_mock.name}"
    assert error_msg in response["error"].get("message")
    assert error_msg in caplog.text
    front_camera_mock.on_webrtc_candidate.assert_called_once()

    # Answer message
    caplog.clear()
    on_message(RingWebRtcMessage(answer="v=0\r\n"))
    response = await client.receive_json()
    event = response.get("event")
    assert event
    assert event.get("type") == "answer"
    assert not caplog.text

    # Unsubscribe/Close session
    front_camera_mock.sync_close_webrtc_stream.assert_not_called()
    await client.send_json_auto_id(
        {
            "type": "unsubscribe_events",
            "subscription": subscription_id,
        }
    )

    response = await client.receive_json()
    assert response
    assert response.get("success") is True
    front_camera_mock.sync_close_webrtc_stream.assert_called_once()