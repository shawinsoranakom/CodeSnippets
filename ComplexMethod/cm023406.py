async def test_hls_max_segments(
    hass: HomeAssistant, setup_component, hls_stream, stream_worker_sync
) -> None:
    """Test rendering the hls playlist with more segments than the segment deque can hold."""
    stream = create_stream(hass, STREAM_SOURCE, {}, dynamic_stream_settings())
    stream_worker_sync.pause()
    hls = stream.add_provider(HLS_PROVIDER)

    hls_client = await hls_stream(stream)

    # Produce enough segments to overfill the output buffer by one
    for sequence in range(MAX_SEGMENTS + 1):
        segment = Segment(sequence=sequence, duration=SEGMENT_DURATION)
        hls.put(segment)
        await hass.async_block_till_done()

    resp = await hls_client.get("/playlist.m3u8")
    assert resp.status == HTTPStatus.OK

    # Only NUM_PLAYLIST_SEGMENTS are returned in the playlist.
    start = MAX_SEGMENTS + 1 - NUM_PLAYLIST_SEGMENTS
    segments = [make_segment(sequence) for sequence in range(start, MAX_SEGMENTS + 1)]
    assert await resp.text() == make_playlist(sequence=start, segments=segments)

    # Fetch the actual segments with a fake byte payload
    for segment in hls.get_segments():
        segment.init = INIT_BYTES
        segment.parts = [
            Part(
                duration=SEGMENT_DURATION,
                has_keyframe=True,
                data=FAKE_PAYLOAD,
            )
        ]

    # The segment that fell off the buffer is not accessible
    with patch.object(hls.stream_settings, "hls_part_timeout", 0.1):
        segment_response = await hls_client.get("/segment/0.m4s")
    assert segment_response.status == HTTPStatus.NOT_FOUND

    # However all segments in the buffer are accessible, even those that were not in the playlist.
    for sequence in range(1, MAX_SEGMENTS + 1):
        segment_response = await hls_client.get(f"/segment/{sequence}.m4s")
        assert segment_response.status == HTTPStatus.OK

    stream_worker_sync.resume()
    await stream.stop()