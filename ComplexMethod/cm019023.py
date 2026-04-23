async def test_cloud_speech(
    hass: HomeAssistant,
    cloud: MagicMock,
    hass_client: ClientSessionGenerator,
    mock_process_stt: AsyncMock,
    expected_response_data: dict[str, Any],
) -> None:
    """Test cloud text-to-speech."""
    cloud.voice.process_stt = mock_process_stt

    assert await async_setup_component(hass, DOMAIN, {"cloud": {}})
    await hass.async_block_till_done()

    on_start_callback = cloud.register_on_start.call_args[0][0]
    await on_start_callback()

    state = hass.states.get("stt.home_assistant_cloud")
    assert state
    assert state.state == STATE_UNKNOWN

    client = await hass_client()

    response = await client.post(
        "/api/stt/stt.home_assistant_cloud",
        headers={
            "X-Speech-Content": (
                "format=wav; codec=pcm; sample_rate=16000; bit_rate=16; channel=1;"
                " language=de-DE"
            )
        },
        data=b"Test",
    )
    response_data = await response.json()

    assert mock_process_stt.call_count == 1
    assert (
        mock_process_stt.call_args.kwargs["content_type"]
        == "audio/wav; codecs=audio/pcm; samplerate=16000"
    )
    assert mock_process_stt.call_args.kwargs["language"] == "de-DE"
    assert response.status == HTTPStatus.OK
    assert response_data == expected_response_data

    state = hass.states.get("stt.home_assistant_cloud")
    assert state
    assert state.state not in (STATE_UNAVAILABLE, STATE_UNKNOWN)