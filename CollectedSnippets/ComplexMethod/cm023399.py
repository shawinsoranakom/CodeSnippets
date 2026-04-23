async def test_ll_hls_playlist_rollover_part(
    hass: HomeAssistant, hls_stream, stream_worker_sync, hls_sync
) -> None:
    """Test playlist request rollover."""

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

    hls_client = await hls_stream(stream)

    # Seed hls with 1 complete segment and 1 in process segment
    for sequence in range(2):
        segment = create_segment(sequence=sequence)
        hls.put(segment)

        for part in create_parts(SEQUENCE_BYTES):
            segment.async_add_part(part, 0)
            hls.part_put()
        complete_segment(segment)

    await hass.async_block_till_done()

    hls_sync.reset_request_pool(4)
    segment = hls.get_segment(1)
    # the first request corresponds to the last part of segment 1
    # the remaining requests correspond to part 0 of segment 2
    requests = asyncio.gather(
        *(
            [
                hls_client.get(
                    f"/playlist.m3u8?_HLS_msn=1&_HLS_part={len(segment.parts) - 1}"
                ),
                hls_client.get(
                    f"/playlist.m3u8?_HLS_msn=1&_HLS_part={len(segment.parts)}"
                ),
                hls_client.get(
                    f"/playlist.m3u8?_HLS_msn=1&_HLS_part={len(segment.parts) + 1}"
                ),
                hls_client.get("/playlist.m3u8?_HLS_msn=2&_HLS_part=0"),
            ]
        )
    )

    await hls_sync.wait_for_handler()

    segment = create_segment(sequence=2)
    hls.put(segment)
    await hass.async_block_till_done()

    remaining_parts = create_parts(SEQUENCE_BYTES)
    segment.async_add_part(remaining_parts.pop(0), 0)
    hls.part_put()

    await hls_sync.wait_for_handler()

    different_response, *same_responses = await requests

    assert different_response.status == HTTPStatus.OK
    assert all(response.status == HTTPStatus.OK for response in same_responses)
    different_playlist = await different_response.read()
    same_playlists = [await response.read() for response in same_responses]
    assert different_playlist != same_playlists[0]
    assert all(playlist == same_playlists[0] for playlist in same_playlists[1:])

    stream_worker_sync.resume()