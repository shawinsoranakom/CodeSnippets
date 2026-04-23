async def create_async_generator(
        cls,
        model: str,
        messages: Messages,
        proxy: str = None,
        prompt: str = None,
        audio: dict = {},
        **kwargs
    ) -> AsyncResult:
        prompt = get_last_message(messages, prompt)
        if not prompt:
            raise ValueError("Prompt is empty.")
        voice = audio.get("voice", model if model and model != cls.model_id else None)
        if not voice:
            voices = await VoicesManager.create()
            if "locale" in audio:
                voices = voices.find(Locale=audio["locale"])
            elif audio.get("language", cls.default_language) != cls.default_language:
                if "-" in audio.get("language"):
                    voices = voices.find(Locale=audio.get("language"))
                else:
                    voices = voices.find(Language=audio.get("language"))
            else:
                voices = voices.find(Locale=cls.default_locale)
            if not voices:
                raise ValueError(f"No voices found for language '{audio.get('language')}' and locale '{audio.get('locale')}'.")
            voice = random.choice(voices)["Name"]

        format = audio.get("format", cls.default_format)
        filename = get_filename([cls.model_id], prompt, f".{format}", prompt)
        target_path = os.path.join(get_media_dir(), filename)
        ensure_media_dir()

        extra_parameters = {param: audio[param] for param in ["rate", "volume", "pitch"] if param in audio}
        communicate = edge_tts.Communicate(prompt, voice=voice, proxy=proxy, **extra_parameters)

        await communicate.save(target_path)
        yield AudioResponse(f"/media/{filename}", voice=voice, text=prompt)