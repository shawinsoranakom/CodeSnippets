def test_silence_seconds() -> None:
    """Test end of voice command silence seconds."""

    segmenter = VoiceCommandSegmenter(silence_seconds=1.0)

    # silence
    assert segmenter.process(_ONE_SECOND, 0.0)
    assert not segmenter.in_command

    # "speech"
    assert segmenter.process(_ONE_SECOND, 1.0)
    assert segmenter.in_command

    # not enough silence to end
    assert segmenter.process(_ONE_SECOND * 0.5, 0.0)
    assert segmenter.in_command

    # exactly enough silence now
    assert not segmenter.process(_ONE_SECOND * 0.5, 0.0)
    assert not segmenter.in_command