async def test_proxy_view(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    wav_file: str,
) -> None:
    """Test proxy HTTP view for converting audio."""
    device_id = "1234"

    await async_setup_component(hass, esphome.DOMAIN, {esphome.DOMAIN: {}})
    client = await hass_client()

    wav_url = pathname2url(wav_file)
    convert_id = "test-id"
    url = f"/api/esphome/ffmpeg_proxy/{device_id}/{convert_id}.mp3"

    # Should fail because we haven't allowed the URL yet
    req = await client.get(url)
    assert req.status == HTTPStatus.NOT_FOUND

    # Allow the URL
    with patch(
        "homeassistant.components.esphome.ffmpeg_proxy.secrets.token_urlsafe",
        return_value=convert_id,
    ):
        assert (
            async_create_proxy_url(
                hass, device_id, wav_url, media_format="mp3", rate=22050, channels=2
            )
            == url
        )

    # Requesting the wrong media format should fail
    wrong_url = f"/api/esphome/ffmpeg_proxy/{device_id}/{convert_id}.flac"
    req = await client.get(wrong_url)
    assert req.status == HTTPStatus.BAD_REQUEST

    # Correct URL
    req = await client.get(url)
    assert req.status == HTTPStatus.OK

    mp3_data = await req.content.read()

    # Verify conversion
    with io.BytesIO(mp3_data) as mp3_io:
        mp3_file = mutagen.File(mp3_io)
        assert mp3_file.info.sample_rate == 22050
        assert mp3_file.info.channels == 2

        # About a second, but not exact
        assert round(mp3_file.info.length, 0) == 1