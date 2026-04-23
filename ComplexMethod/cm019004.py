async def test_provider_properties(
    hass: HomeAssistant,
    cloud: MagicMock,
    engine_id: str,
) -> None:
    """Test cloud provider."""
    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
    await hass.async_block_till_done()
    on_start_callback = cloud.register_on_start.call_args[0][0]
    await on_start_callback()

    engine = get_engine_instance(hass, engine_id)

    assert engine is not None
    assert engine.supported_options == ["gender", "voice", "audio_output"]
    assert "nl-NL" in engine.supported_languages
    supported_voices = engine.async_get_supported_voices("nl-NL")
    assert supported_voices is not None
    assert Voice("ColetteNeural", "Colette") in supported_voices
    supported_voices = engine.async_get_supported_voices("missing_language")
    assert supported_voices is None