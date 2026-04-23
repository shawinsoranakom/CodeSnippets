async def test_send_text_command_media_player(
    hass: HomeAssistant,
    setup_integration: ComponentSetup,
    hass_client: ClientSessionGenerator,
    freezer: FrozenDateTimeFactory,
) -> None:
    """Test send_text_command with media_player."""
    await setup_integration()

    play_media_calls = async_mock_service(hass, "media_player", "play_media")

    command = "tell me a joke"
    media_player = "media_player.office_speaker"
    audio_response1 = b"joke1 audio response bytes"
    audio_response2 = b"joke2 audio response bytes"
    with patch(
        "homeassistant.components.google_assistant_sdk.helpers.TextAssistant.assist",
        side_effect=[
            ("joke1 text", None, audio_response1),
            ("joke2 text", None, audio_response2),
        ],
    ) as mock_assist_call:
        # Run the same command twice, getting different audio response each time.
        await hass.services.async_call(
            DOMAIN,
            "send_text_command",
            {
                "command": command,
                "media_player": media_player,
            },
            blocking=True,
        )
        await hass.services.async_call(
            DOMAIN,
            "send_text_command",
            {
                "command": command,
                "media_player": media_player,
            },
            blocking=True,
        )

    mock_assist_call.assert_has_calls([call(command), call(command)])
    assert len(play_media_calls) == 2
    for play_media_call in play_media_calls:
        assert play_media_call.data["entity_id"] == [media_player]
        assert play_media_call.data["media_content_id"].startswith(
            "/api/google_assistant_sdk/audio/"
        )

    audio_url1 = play_media_calls[0].data["media_content_id"]
    audio_url2 = play_media_calls[1].data["media_content_id"]
    assert audio_url1 != audio_url2

    # Assert that both audio responses can be served
    status, response = await fetch_api_url(hass_client, audio_url1)
    assert status == http.HTTPStatus.OK
    assert response == audio_response1
    status, response = await fetch_api_url(hass_client, audio_url2)
    assert status == http.HTTPStatus.OK
    assert response == audio_response2

    # Assert a nonexistent URL returns 404
    status, _ = await fetch_api_url(
        hass_client, "/api/google_assistant_sdk/audio/nonexistent"
    )
    assert status == http.HTTPStatus.NOT_FOUND

    # Assert that both audio responses can still be served before the 5 minutes expiration
    freezer.tick(timedelta(minutes=4, seconds=59))
    async_fire_time_changed(hass)
    status, response = await fetch_api_url(hass_client, audio_url1)
    assert status == http.HTTPStatus.OK
    assert response == audio_response1
    status, response = await fetch_api_url(hass_client, audio_url2)
    assert status == http.HTTPStatus.OK
    assert response == audio_response2

    # Assert that they cannot be served after the 5 minutes expiration
    freezer.tick(timedelta(seconds=2))
    async_fire_time_changed(hass)
    status, _ = await fetch_api_url(hass_client, audio_url1)
    assert status == http.HTTPStatus.NOT_FOUND
    status, _ = await fetch_api_url(hass_client, audio_url2)
    assert status == http.HTTPStatus.NOT_FOUND