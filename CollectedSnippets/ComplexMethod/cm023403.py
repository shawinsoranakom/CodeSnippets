async def test_durations(hass: HomeAssistant, worker_finished_stream) -> None:
    """Test that the duration metadata matches the media."""

    # Use a target part duration which has a slight mismatch
    # with the incoming frame rate to better expose problems.
    target_part_duration = TEST_PART_DURATION - 0.01
    await async_setup_component(
        hass,
        "stream",
        {
            "stream": {
                CONF_LL_HLS: True,
                CONF_SEGMENT_DURATION: SEGMENT_DURATION,
                CONF_PART_DURATION: target_part_duration,
            }
        },
    )

    source = generate_h264_video(
        duration=round(SEGMENT_DURATION + target_part_duration + 1)
    )
    worker_finished, mock_stream = worker_finished_stream

    with patch("homeassistant.components.stream.Stream", wraps=mock_stream):
        stream = create_stream(
            hass, source, {}, dynamic_stream_settings(), stream_label="camera"
        )

    recorder_output = stream.add_provider(RECORDER_PROVIDER, timeout=30)
    await stream.start()
    await worker_finished.wait()

    complete_segments = list(recorder_output.get_segments())[:-1]

    assert len(complete_segments) >= 1

    # check that the Part duration metadata matches the durations in the media
    running_metadata_duration = 0
    for segment in complete_segments:
        av_segment = av.open(io.BytesIO(segment.init + segment.get_data()))
        av_segment.close()
        for part_num, part in enumerate(segment.parts):
            av_part = av.open(io.BytesIO(segment.init + part.data))
            running_metadata_duration += part.duration
            # av_part.duration actually returns the dts of the first packet of the next
            # av_part. When we normalize this by av.time_base we get the running
            # duration of the media.
            # The metadata duration may differ slightly from the media duration.
            # The worker has some flexibility of where to set each metadata boundary,
            # and when the media's duration is slightly too long or too short, the
            # metadata duration may be adjusted up or down.
            # We check here that the divergence between the metadata duration and the
            # media duration is not too large (2 frames seems reasonable here).
            assert math.isclose(
                (av_part.duration - av_part.start_time) / av.time_base,
                part.duration,
                abs_tol=2 / av_part.streams.video[0].average_rate + 1e-6,
            )
            # Also check that the sum of the durations so far matches the last dts
            # in the media.
            assert math.isclose(
                running_metadata_duration,
                av_part.duration / av.time_base,
                abs_tol=1e-6,
            )
            # And check that the metadata duration is between 0.85x and 1.0x of
            # the part target duration
            if not (part.has_keyframe or part_num == len(segment.parts) - 1):
                assert part.duration > 0.85 * target_part_duration - 1e-6
            assert part.duration < target_part_duration + 1e-6
            av_part.close()
    # check that the Part durations are consistent with the Segment durations
    for segment in complete_segments:
        assert math.isclose(
            sum(part.duration for part in segment.parts),
            segment.duration,
            abs_tol=1e-6,
        )

    await stream.stop()