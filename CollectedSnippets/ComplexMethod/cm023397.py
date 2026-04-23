async def test_ll_hls_playlist_view(
    hass: HomeAssistant, hls_stream, stream_worker_sync
) -> None:
    """Test rendering the hls playlist with 1 and 2 output segments."""
    await async_setup_component(
        hass,
        "stream",
        {
            "stream": {
                CONF_LL_HLS: True,
                CONF_SEGMENT_DURATION: SEGMENT_DURATION,
                CONF_PART_DURATION: TEST_PART_DURATION,
            }
        },
    )

    stream = create_stream(hass, STREAM_SOURCE, {}, dynamic_stream_settings())
    stream_worker_sync.pause()
    hls = stream.add_provider(HLS_PROVIDER)

    # Add 2 complete segments to output
    for sequence in range(2):
        segment = create_segment(sequence=sequence)
        hls.put(segment)
        for part in create_parts(SEQUENCE_BYTES):
            segment.async_add_part(part, 0)
            hls.part_put()
        complete_segment(segment)
    await hass.async_block_till_done()

    hls_client = await hls_stream(stream)

    resp = await hls_client.get("/playlist.m3u8")
    assert resp.status == HTTPStatus.OK
    assert await resp.text() == make_playlist(
        sequence=0,
        segments=[
            make_segment_with_parts(i, len(segment.parts), PART_INDEPENDENT_PERIOD)
            for i in range(2)
        ],
        hint=make_hint(2, 0),
        segment_duration=SEGMENT_DURATION,
        part_target_duration=hls.stream_settings.part_target_duration,
    )

    # add one more segment
    segment = create_segment(sequence=2)
    hls.put(segment)
    for part in create_parts(SEQUENCE_BYTES):
        segment.async_add_part(part, 0)
        hls.part_put()
    complete_segment(segment)

    await hass.async_block_till_done()
    resp = await hls_client.get("/playlist.m3u8")
    assert resp.status == HTTPStatus.OK
    assert await resp.text() == make_playlist(
        sequence=0,
        segments=[
            make_segment_with_parts(i, len(segment.parts), PART_INDEPENDENT_PERIOD)
            for i in range(3)
        ],
        hint=make_hint(3, 0),
        segment_duration=SEGMENT_DURATION,
        part_target_duration=hls.stream_settings.part_target_duration,
    )

    stream_worker_sync.resume()
    await stream.stop()