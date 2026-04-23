def create_podcast(
    script: Any,
    output_path: str,
    tts_engine: str = "openai",
    language_code: str = "en",
    silence_duration: float = 0.7,
    voice_map: Dict[int, str] = None,
    model: str = TTS_MODEL,
) -> Optional[str]:
    if tts_engine.lower() != "openai":
        print(f"Only OpenAI TTS engine is available in this standalone version. Requested: {tts_engine}")
        return None
    try:
        api_key = load_api_key("OPENAI_API_KEY")
        if not api_key:
            print("No OpenAI API key provided")
            return None
        client = OpenAI(api_key=api_key)
        print("OpenAI client initialized")
    except Exception as e:
        print(f"Failed to initialize OpenAI client: {e}")
        return None
    output_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if voice_map is None:
        voice_map = DEFAULT_VOICE_MAP.copy()
    model_to_use = model
    if model == "tts-1" and language_code == "en":
        model_to_use = "tts-1-hd"
        print(f"Using high-definition TTS model for English: {model_to_use}")
    generated_segments = []
    sampling_rate_detected = None

    if hasattr(script, "entries"):
        entries = script.entries
    else:
        entries = script

    print(f"Processing {len(entries)} script entries")
    for i, entry in enumerate(entries):
        if hasattr(entry, "speaker"):
            speaker_id = entry.speaker
            entry_text = entry.text
        else:
            speaker_id = entry["speaker"]
            entry_text = entry["text"]
        print(f"Processing entry {i + 1}/{len(entries)}: Speaker {speaker_id}")
        result = text_to_speech_openai(
            client=client,
            text=entry_text,
            speaker_id=speaker_id,
            voice_map=voice_map,
            model=model_to_use,
        )
        if result:
            segment_audio, segment_rate = result
            if sampling_rate_detected is None:
                sampling_rate_detected = segment_rate
                print(f"Using sample rate: {sampling_rate_detected} Hz")
            elif sampling_rate_detected != segment_rate:
                print(f"Sample rate mismatch: {sampling_rate_detected} vs {segment_rate}")
                try:
                    segment_audio = resample_audio(segment_audio, segment_rate, sampling_rate_detected)
                    print(f"Resampled to {sampling_rate_detected} Hz")
                except Exception as e:
                    sampling_rate_detected = segment_rate
                    print(f"Resampling failed: {e}")
            generated_segments.append(segment_audio)
        else:
            print(f"Failed to generate audio for entry {i + 1}")
    if not generated_segments:
        print("No audio segments were generated")
        return None
    if sampling_rate_detected is None:
        print("Could not determine sample rate")
        return None
    print(f"Combining {len(generated_segments)} audio segments")
    full_audio = combine_audio_segments(generated_segments, silence_duration, sampling_rate_detected)
    if full_audio.size == 0:
        print("Combined audio is empty")
        return None

    try:
        if os.path.exists(INTRO_MUSIC_FILE):
            intro_music, intro_sr = sf.read(INTRO_MUSIC_FILE)
            print(f"Loaded intro music: {len(intro_music) / intro_sr:.1f} seconds")

            if intro_music.ndim == 2:
                intro_music = np.mean(intro_music, axis=1)

            if intro_sr != sampling_rate_detected:
                intro_music = resample_audio_scipy(intro_music, intro_sr, sampling_rate_detected)

            full_audio = np.concatenate([intro_music, full_audio])
            print("Added intro music")

        if os.path.exists(OUTRO_MUSIC_FILE):
            outro_music, outro_sr = sf.read(OUTRO_MUSIC_FILE)
            print(f"Loaded outro music: {len(outro_music) / outro_sr:.1f} seconds")

            if outro_music.ndim == 2:
                outro_music = np.mean(outro_music, axis=1)

            if outro_sr != sampling_rate_detected:
                outro_music = resample_audio_scipy(outro_music, outro_sr, sampling_rate_detected)

            full_audio = np.concatenate([full_audio, outro_music])
            print("Added outro music")

    except Exception as e:
        print(f"Could not add intro/outro music: {e}")
        print("Continuing without background music")

    print(f"Writing audio to {output_path}")
    try:
        sf.write(output_path, full_audio, sampling_rate_detected)
    except Exception as e:
        print(f"Failed to write audio file: {e}")
        return None
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path)
        print(f"Audio file created: {output_path} ({file_size / 1024:.1f} KB)")
        return output_path
    else:
        print(f"Failed to create audio file at {output_path}")
        return None