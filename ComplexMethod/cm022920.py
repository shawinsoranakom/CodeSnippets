def test_timeout() -> None:
    """Test that voice command detection times out."""

    segmenter = VoiceCommandSegmenter(timeout_seconds=1.0)

    # not enough to time out
    assert not segmenter.timed_out
    assert segmenter.process(_ONE_SECOND * 0.5, 0.0)
    assert not segmenter.timed_out

    # enough to time out
    assert not segmenter.process(_ONE_SECOND * 0.5, 1.0)
    assert segmenter.timed_out

    # flag resets with more audio
    assert segmenter.process(_ONE_SECOND * 0.5, 1.0)
    assert not segmenter.timed_out

    assert not segmenter.process(_ONE_SECOND * 0.5, 0.0)
    assert segmenter.timed_out