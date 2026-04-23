async def execute(
        cls,
        audio: Input.Audio,
        model: dict,
        language_code: str,
        num_speakers: int,
        seed: int,
    ) -> IO.NodeOutput:
        if model["diarize"] and num_speakers:
            raise ValueError(
                "Number of speakers cannot be specified when diarization is enabled. "
                "Either disable diarization or set num_speakers to 0."
            )
        request = SpeechToTextRequest(
            model_id=model["model"],
            cloud_storage_url=await upload_audio_to_comfyapi(
                cls, audio, container_format="mp4", codec_name="aac", mime_type="audio/mp4"
            ),
            language_code=language_code if language_code.strip() else None,
            tag_audio_events=model["tag_audio_events"],
            num_speakers=num_speakers if num_speakers > 0 else None,
            timestamps_granularity=model["timestamps_granularity"],
            diarize=model["diarize"],
            diarization_threshold=model["diarization_threshold"] if model["diarize"] else None,
            seed=seed,
            temperature=model["temperature"],
        )
        response = await sync_op(
            cls,
            ApiEndpoint(path="/proxy/elevenlabs/v1/speech-to-text", method="POST"),
            response_model=SpeechToTextResponse,
            data=request,
            content_type="multipart/form-data",
        )
        words_json = json.dumps(
            [w.model_dump(exclude_none=True) for w in response.words] if response.words else [],
            indent=2,
        )
        return IO.NodeOutput(response.text, response.language_code, words_json)