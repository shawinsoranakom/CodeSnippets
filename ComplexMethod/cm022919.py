def test_speech_reset() -> None:
    """Test that silence resets start of voice command detection."""

    segmenter = VoiceCommandSegmenter(
        silence_seconds=1.0, reset_seconds=0.5, speech_seconds=1.0
    )

    # silence
    assert segmenter.process(_ONE_SECOND, 0.0)
    assert not segmenter.in_command

    # not enough speech to start voice command
    assert segmenter.process(_ONE_SECOND * 0.5, 1.0)
    assert not segmenter.in_command

    # silence should reset speech detection
    assert segmenter.process(_ONE_SECOND, 0.0)
    assert not segmenter.in_command

    # not enough speech to start voice command
    assert segmenter.process(_ONE_SECOND * 0.5, 1.0)
    assert not segmenter.in_command

    # exactly enough speech now
    assert segmenter.process(_ONE_SECOND * 0.5, 1.0)
    assert segmenter.in_command