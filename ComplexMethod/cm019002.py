async def test_prefs_default_voice(
    hass: HomeAssistant,
    cloud: MagicMock,
    set_cloud_prefs: Callable[[dict[str, Any]], Coroutine[Any, Any, None]],
    engine_id: str,
    platform_config: dict[str, Any] | None,
) -> None:
    """Test cloud provider uses the preferences."""
    assert await async_setup_component(hass, "homeassistant", {})
    assert await async_setup_component(hass, TTS_DOMAIN, {TTS_DOMAIN: platform_config})
    await hass.async_block_till_done()
    assert await async_setup_component(hass, DOMAIN, {DOMAIN: {}})
    await hass.async_block_till_done()

    assert cloud.client.prefs.tts_default_voice == ("en-US", "JennyNeural")

    on_start_callback = cloud.register_on_start.call_args[0][0]
    await on_start_callback()
    await hass.async_block_till_done()

    engine = get_engine_instance(hass, engine_id)

    assert engine is not None
    # The platform config provider will be overridden by the discovery info provider.
    assert engine.default_language == "en-US"
    assert engine.default_options == {"audio_output": "mp3"}

    await set_cloud_prefs({"tts_default_voice": ("nl-NL", "MaartenNeural")})
    await hass.async_block_till_done()

    assert engine.default_language == "nl-NL"
    assert engine.default_options == {"audio_output": "mp3"}