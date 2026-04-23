async def _test_setup_and_signaling(
    hass: HomeAssistant,
    issue_registry: ir.IssueRegistry,
    rest_client: AsyncMock,
    ws_client: Mock,
    config: ConfigType,
    after_setup_fn: Callable[[], None],
    camera: MockCamera,
) -> None:
    """Test the go2rtc config entry."""
    entity_id = camera.entity_id
    assert camera.camera_capabilities.frontend_stream_types == {StreamType.HLS}

    assert await async_setup_component(hass, DOMAIN, config)
    await hass.async_block_till_done(wait_background_tasks=True)
    assert issue_registry.async_get_issue(DOMAIN, "recommended_version") is None
    config_entries = hass.config_entries.async_entries(DOMAIN)
    assert len(config_entries) == 1
    config_entry = config_entries[0]
    assert config_entry.state is ConfigEntryState.LOADED
    after_setup_fn()

    receive_message_callback = Mock(spec_set=WebRTCSendMessage)

    sessions = []

    async def test(session: str) -> None:
        sessions.append(session)
        await camera.async_handle_async_webrtc_offer(
            OFFER_SDP, session, receive_message_callback
        )
        ws_client.send.assert_called_once_with(
            WebRTCOffer(
                OFFER_SDP,
                camera.async_get_webrtc_client_configuration().configuration.ice_servers,
            )
        )
        ws_client.subscribe.assert_called_once()

        # Simulate the answer from the go2rtc server
        callback = ws_client.subscribe.call_args[0][0]
        callback(WebRTCAnswer(ANSWER_SDP))
        receive_message_callback.assert_called_once_with(HAWebRTCAnswer(ANSWER_SDP))

    await test("sesion_1")

    rest_client.streams.add.assert_called_once_with(
        entity_id,
        [
            "rtsp://stream",
            f"ffmpeg:{camera.entity_id}#audio=opus#query=log_level=debug",
        ],
    )

    # Stream exists but the source is different
    rest_client.streams.add.reset_mock()
    rest_client.streams.list.return_value = {
        entity_id: Stream([Producer("rtsp://different")])
    }

    receive_message_callback.reset_mock()
    ws_client.reset_mock()
    await test("session_2")

    rest_client.streams.add.assert_called_once_with(
        entity_id,
        [
            "rtsp://stream",
            f"ffmpeg:{camera.entity_id}#audio=opus#query=log_level=debug",
        ],
    )

    # If the stream is already added, the stream should not be added again.
    rest_client.streams.add.reset_mock()
    rest_client.streams.list.return_value = {
        entity_id: Stream([Producer("rtsp://stream")])
    }

    receive_message_callback.reset_mock()
    ws_client.reset_mock()
    await test("session_3")

    rest_client.streams.add.assert_not_called()
    assert isinstance(camera._webrtc_provider, WebRTCProvider)

    provider = camera._webrtc_provider
    for session in sessions:
        assert session in provider._sessions

    with patch.object(provider, "teardown", wraps=provider.teardown) as teardown:
        # Set stream source to None and provider should be skipped
        rest_client.streams.list.return_value = {}
        receive_message_callback.reset_mock()
        camera.set_stream_source(None)
        await camera.async_handle_async_webrtc_offer(
            OFFER_SDP, "session_id", receive_message_callback
        )
        receive_message_callback.assert_called_once_with(
            WebRTCError("go2rtc_webrtc_offer_failed", "Camera has no stream source")
        )
        teardown.assert_called_once()
        # We use one ws_client mock for all sessions
        assert ws_client.close.call_count == len(sessions)

        await hass.config_entries.async_unload(config_entry.entry_id)
        await hass.async_block_till_done()
        assert config_entry.state is ConfigEntryState.NOT_LOADED
        assert teardown.call_count == 2