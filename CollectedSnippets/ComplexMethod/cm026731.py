async def get_voices_models(
    hass: HomeAssistant, api_key: str
) -> tuple[dict[str, str], dict[str, str]]:
    """Get available voices and models as dicts."""
    httpx_client = get_async_client(hass)
    client = AsyncElevenLabs(api_key=api_key, httpx_client=httpx_client)
    voices = (await client.voices.get_all()).voices
    models = await client.models.list()

    voices_dict = {
        voice.voice_id: voice.name
        for voice in sorted(voices, key=lambda v: v.name or "")
        if voice.name
    }
    models_dict = {
        model.model_id: model.name
        for model in sorted(models, key=lambda m: m.name or "")
        if model.name and model.can_do_text_to_speech
    }
    return voices_dict, models_dict