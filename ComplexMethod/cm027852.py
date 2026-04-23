def text_to_speech_openai(
    client: OpenAI,
    text: str,
    speaker_id: int,
    voice_map: Dict[int, str] = None,
    model: str = TTS_MODEL,
) -> Optional[Tuple[np.ndarray, int]]:
    if not text.strip():
        print("Empty text provided, skipping TTS generation")
        return None
    voice_map = voice_map or DEFAULT_VOICE_MAP
    voice = voice_map.get(speaker_id)
    if not voice:
        if speaker_id in OPENAI_VOICES:
            voice = OPENAI_VOICES[speaker_id]
        else:
            voice = next(iter(voice_map.values()), "alloy")
        print(f"No voice mapping for speaker {speaker_id}, using {voice}")
    try:
        print(f"Generating TTS for speaker {speaker_id} using voice '{voice}'")
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            response_format="mp3",
        )
        audio_data = response.content
        if not audio_data:
            print("OpenAI TTS returned empty response")
            return None
        print(f"Received {len(audio_data)} bytes from OpenAI TTS")
        temp_file = tempfile.NamedTemporaryFile(suffix=".mp3", delete=False)
        temp_path = temp_file.name
        temp_file.close()
        with open(temp_path, "wb") as f:
            f.write(audio_data)
        try:
            return process_audio_file(temp_path)
        finally:
            if os.path.exists(temp_path):
                os.unlink(temp_path)
    except Exception as e:
        print(f"OpenAI TTS API error: {e}")
        import traceback

        traceback.print_exc()
        return None