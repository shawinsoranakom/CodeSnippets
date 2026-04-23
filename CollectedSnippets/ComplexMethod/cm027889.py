def create_podcast(
    script: Any,
    output_path: str,
    silence_duration: float = 0.7,
    sampling_rate: int = 24000,
    lang_code: str = "en",
    model: str = TEXT_TO_SPEECH_MODEL,
    voice_map: Dict[int, str] = None,
    api_key: str = None,
) -> Optional[str]:
    try:
        if not api_key:
            api_key = load_api_key()
            if not api_key:
                print("ERROR: No OpenAI API key provided")
                return None
        client = OpenAI(api_key=api_key)
        print("INFO: OpenAI client initialized")
    except Exception as e:
        print(f"ERROR: Failed to initialize OpenAI client: {e}")
        return None
    output_path = os.path.abspath(output_path)
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    if voice_map is None:
        voice_map = DEFAULT_VOICE_MAP.copy()
    model_to_use = model
    if model == "tts-1" and lang_code == "en":
        model_to_use = "tts-1-hd"
        print(f"INFO: Using high-definition TTS model for English: {model_to_use}")
    generated_segments = []
    sampling_rate_detected = None
    entries = script.entries if hasattr(script, "entries") else script
    print(f"INFO: Processing {len(entries)} script entries")
    for i, entry in enumerate(entries):
        if hasattr(entry, "speaker"):
            speaker_id = entry.speaker
            entry_text = entry.text
        else:
            speaker_id = entry["speaker"]
            entry_text = entry["text"]
        print(f"INFO: Processing entry {i + 1}/{len(entries)}: Speaker {speaker_id}")
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
                print(f"INFO: Using sample rate: {sampling_rate_detected} Hz")
            elif sampling_rate_detected != segment_rate:
                print(f"WARNING: Sample rate mismatch: {sampling_rate_detected} vs {segment_rate}")
                try:
                    import librosa

                    segment_audio = librosa.resample(segment_audio, orig_sr=segment_rate, target_sr=sampling_rate_detected)
                    print(f"INFO: Resampled to {sampling_rate_detected} Hz")
                except ImportError:
                    sampling_rate_detected = segment_rate
                    print(f"WARNING: Librosa not available for resampling, using {segment_rate} Hz")
                except Exception as e:
                    print(f"ERROR: Resampling failed: {e}")
            generated_segments.append(segment_audio)
        else:
            print(f"WARNING: Failed to generate audio for entry {i + 1}")
    if not generated_segments:
        print("ERROR: No audio segments were generated")
        return None
    if sampling_rate_detected is None:
        print("ERROR: Could not determine sample rate")
        return None
    print(f"INFO: Combining {len(generated_segments)} audio segments")
    full_audio = combine_audio_segments(generated_segments, silence_duration, sampling_rate_detected)
    if full_audio.size == 0:
        print("ERROR: Combined audio is empty")
        return None
    print(f"INFO: Writing audio to {output_path}")
    try:
        sf.write(output_path, full_audio, sampling_rate_detected)
    except Exception as e:
        print(f"ERROR: Failed to write audio file: {e}")
        return None
    if os.path.exists(output_path):
        file_size = os.path.getsize(output_path)
        print(f"INFO: Audio file created: {output_path} ({file_size / 1024:.1f} KB)")
        return output_path
    else:
        print(f"ERROR: Failed to create audio file at {output_path}")
        return None