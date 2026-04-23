def text_to_speech_elevenlabs(
    client: ElevenLabs,
    text: str,
    speaker_id: int,
    voice_map={1: "Rachel", 2: "Adam"},
    model_id: str = TEXT_TO_SPEECH_MODEL,
) -> Optional[Tuple[np.ndarray, int]]:
    if not text.strip():
        return None
    voice_name_or_id = voice_map.get(speaker_id)
    if not voice_name_or_id:
        print(f"No voice found for speaker_id {speaker_id}")
        return None
    try:
        from pydub import AudioSegment

        pydub_available = True
    except ImportError:
        pydub_available = False
    try:
        audio_generator = client.generate(
            text=text,
            voice=voice_name_or_id,
            model=model_id,
            stream=True,
        )
        audio_chunks = []
        for chunk in audio_generator:
            if chunk:
                audio_chunks.append(chunk)
        if not audio_chunks:
            return None
        audio_data = b"".join(audio_chunks)
        with tempfile.NamedTemporaryFile(suffix=".mp3", delete=False) as temp_file:
            temp_path = temp_file.name
            temp_file.write(audio_data)
        if pydub_available:
            try:
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
            except Exception as pydub_error:
                print(f"Pydub processing failed: {pydub_error}")
        try:
            audio_np, samplerate = sf.read(temp_path)
            os.unlink(temp_path)
            return audio_np, samplerate
        except Exception as _:
            if pydub_available:
                try:
                    sound = AudioSegment.from_mp3(temp_path)
                    wav_path = temp_path.replace(".mp3", ".wav")
                    sound.export(wav_path, format="wav")

                    audio_np, samplerate = sf.read(wav_path)
                    os.unlink(temp_path)
                    os.unlink(wav_path)
                    return audio_np, samplerate
                except Exception:
                    pass
        if os.path.exists(temp_path):
            os.unlink(temp_path)
        return None

    except Exception as e:
        print(f"Error during ElevenLabs API call: {e}")
        import traceback

        traceback.print_exc()
        return None