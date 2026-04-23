async def test_transcription_with_enable_force_include_usage(
    transcription_client_with_force_include_usage, winning_call
):
    res = (
        await transcription_client_with_force_include_usage.audio.transcriptions.create(
            model="openai/whisper-large-v3-turbo",
            file=winning_call,
            language="en",
            temperature=0.0,
            stream=True,
            timeout=30,
        )
    )

    async for chunk in res:
        if not len(chunk.choices):
            # final usage sent
            usage = chunk.usage
            assert isinstance(usage, dict)
            assert usage["prompt_tokens"] > 0
            assert usage["completion_tokens"] > 0
            assert usage["total_tokens"] > 0
        else:
            assert not hasattr(chunk, "usage")