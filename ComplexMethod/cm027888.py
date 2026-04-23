def text_to_speech_openai(
    client: OpenAI,
    text: str,
    speaker_id: int,
    voice_map: Dict[int, str] = None,
    model: str = TEXT_TO_SPEECH_MODEL,
) -> Optional[Tuple[np.ndarray, int]]:
    if not text.strip():
        print("WARNING: Empty text provided, skipping TTS generation")
        return None
    voice_map = voice_map or DEFAULT_VOICE_MAP
    voice = voice_map.get(speaker_id)
    if not voice:
        if speaker_id in OPENAI_VOICES:
            voice = OPENAI_VOICES[speaker_id]
        else:
            voice = next(iter(voice_map.values()), "alloy")
        print(f"WARNING: No voice mapping for speaker {speaker_id}, using {voice}")
    try:
        print(f"INFO: Generating TTS for speaker {speaker_id} using voice '{voice}'")
        response = client.audio.speech.create(
            model=model,
            voice=voice,
            input=text,
            response_format="mp3",
        )
        audio_data = response.content
        if not audio_data:
            print("ERROR: OpenAI TTS returned empty response")
            return None
        print(f"INFO: Received {len(audio_data)} bytes from OpenAI TTS")
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(audio_data)
        try:
            from pydub import AudioSegment

            audio_segment = AudioSegment.from_mp3(temp_path)
            channels = audio_segment.channels
            sample_width = audio_segment.sample_width
            frame_rate = audio_segment.frame_rate
            samples = np.array(audio_segment.get_array_of_samples())
            if channels == 2:
                samples = samples.reshape(-1, 2).mean(axis=1)
            max_possible_value = float(2 ** (8 * sample_width - 1))
            samples = samples.astype(np.float32) / max_possible_value
            os.unlink(temp_path)
            return samples, frame_rate
        except ImportError:
            print("WARNING: Pydub not available, falling back to soundfile")
        except Exception as e:
            print(f"ERROR: Pydub processing failed: {e}")
        try:
            audio_np, samplerate = sf.read(temp_path)
            os.unlink(temp_path)
            return audio_np, samplerate
        except Exception as e:
            print(f"ERROR: Failed to process audio with soundfile: {e}")
            try:
                from pydub import AudioSegment

                sound = AudioSegment.from_mp3(temp_path)
                wav_path = temp_path.replace(".mp3", ".wav")
                sound.export(wav_path, format="wav")
                audio_np, samplerate = sf.read(wav_path)
                os.unlink(temp_path)
                os.unlink(wav_path)
                return audio_np, samplerate
            except Exception as e:
                print(f"ERROR: All audio processing methods failed: {e}")
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        return None

    except Exception as e:
        print(f"ERROR: OpenAI TTS API error: {e}")
        import traceback

        traceback.print_exc()
        return None