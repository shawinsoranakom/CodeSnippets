async def test_stream_audio_uses_enum_values(
    hass: HomeAssistant,
    hass_client: ClientSessionGenerator,
    setup: MockSTTProvider | MockSTTProviderEntity,
) -> None:
    """Test that HTTP API passes enum values to async_process_audio_stream."""
    client = await hass_client()
    response = await client.post(
        f"/api/stt/{setup.url_path}",
        headers={
            "X-Speech-Content": (
                "format=wav; codec=pcm; sample_rate=16000; bit_rate=16; channel=1;"
                " language=en"
            )
        },
    )
    assert response.status == HTTPStatus.OK

    assert len(setup.calls) == 1
    metadata, _ = setup.calls[0]

    assert isinstance(metadata.format, AudioFormats)
    assert metadata.format == AudioFormats.WAV
    assert isinstance(metadata.codec, AudioCodecs)
    assert metadata.codec == AudioCodecs.PCM
    assert isinstance(metadata.bit_rate, AudioBitRates)
    assert metadata.bit_rate == AudioBitRates.BITRATE_16
    assert isinstance(metadata.sample_rate, AudioSampleRates)
    assert metadata.sample_rate == AudioSampleRates.SAMPLERATE_16000
    assert isinstance(metadata.channel, AudioChannels)
    assert metadata.channel == AudioChannels.CHANNEL_MONO