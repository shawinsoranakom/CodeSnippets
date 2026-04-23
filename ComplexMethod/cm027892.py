def create_podcast(
    script: Any,
    output_path: str,
    silence_duration: float = 0.7,
    sampling_rate: int = 24_000,
    lang_code: str = "en",
    elevenlabs_model: str = "eleven_multilingual_v2",
    voice_map: dict = {1: "Rachel", 2: "Adam"},
    api_key: str = None,
) -> str:
    if not api_key:
        print("Warning: Using hardcoded API key")
    try:
        client = ElevenLabs(api_key=api_key)
        try:
            voices = client.voices.get_all()
            print(f"API connection successful. Found {len(voices)} available voices.")
        except Exception as voice_error:
            print(f"Warning: Could not retrieve voices: {voice_error}")
    except Exception as e:
        print(f"Fatal Error: Failed to initialize ElevenLabs client: {e}")
        return None
    output_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    generated_segments = []
    determined_sampling_rate = -1
    entries = script.entries if hasattr(script, "entries") else script
    for i, entry in enumerate(entries):
        if hasattr(entry, "speaker"):
            speaker_id = entry.speaker
            entry_text = entry.text
        else:
            speaker_id = entry["speaker"]
            entry_text = entry["text"]
        result = text_to_speech_elevenlabs(
            client=client,
            text=entry_text,
            speaker_id=speaker_id,
            voice_map=voice_map,
            model_id=elevenlabs_model,
        )
        if result:
            segment_audio, segment_rate = result

            if determined_sampling_rate == -1:
                determined_sampling_rate = segment_rate
            elif determined_sampling_rate != segment_rate:
                try:
                    import librosa

                    segment_audio = librosa.resample(
                        segment_audio,
                        orig_sr=segment_rate,
                        target_sr=determined_sampling_rate,
                    )
                except ImportError:
                    determined_sampling_rate = segment_rate
                except Exception:
                    pass
            generated_segments.append(segment_audio)
    if not generated_segments or determined_sampling_rate <= 0:
        return None
    full_audio = combine_audio_segments(generated_segments, silence_duration, determined_sampling_rate)
    if full_audio.size == 0:
        return None
    write_to_disk(output_path, full_audio, determined_sampling_rate)
    if os.path.exists(output_path):
        return output_path
    else:
        return None