def test_silence_reset() -> None:
    """Test that speech resets end of voice command detection."""

    segmenter = VoiceCommandSegmenter(silence_seconds=1.0, reset_seconds=0.5)

    # silence
    assert segmenter.process(_ONE_SECOND, 0.0)
    assert not segmenter.in_command

    # "speech"
    assert segmenter.process(_ONE_SECOND, 1.0)
    assert segmenter.in_command

    # not enough silence to end
    assert segmenter.process(_ONE_SECOND * 0.5, 0.0)
    assert segmenter.in_command

    # speech should reset silence detection
    assert segmenter.process(_ONE_SECOND * 0.5, 1.0)
    assert segmenter.in_command

    # not enough silence to end
    assert segmenter.process(_ONE_SECOND * 0.5, 0.0)
    assert segmenter.in_command

    # exactly enough silence now
    assert not segmenter.process(_ONE_SECOND * 0.5, 0.0)
    assert not segmenter.in_command