async def test_ll_hls_msn(
    hass: HomeAssistant, hls_stream, stream_worker_sync, hls_sync
) -> None:
    """Test that requests using _HLS_msn get held and returned or rejected."""
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

    # Create 4 requests for sequences 0 through 3
    # 0 and 1 should hold then go through and 2 and 3 should fail immediately.

    hls_sync.reset_request_pool(4)
    msn_requests = asyncio.gather(
        *(hls_client.get(f"/playlist.m3u8?_HLS_msn={i}") for i in range(4))
    )

    for sequence in range(3):
        await hls_sync.wait_for_handler()
        segment = Segment(sequence=sequence, duration=SEGMENT_DURATION)
        hls.put(segment)

    msn_responses = await msn_requests

    assert msn_responses[0].status == HTTPStatus.OK
    assert msn_responses[1].status == HTTPStatus.OK
    assert msn_responses[2].status == HTTPStatus.BAD_REQUEST
    assert msn_responses[3].status == HTTPStatus.BAD_REQUEST

    # Sequence number is now 2. Create six more requests for sequences 0 through 5.
    # Calls for msn 0 through 4 should work, 5 should fail.

    hls_sync.reset_request_pool(6)
    msn_requests = asyncio.gather(
        *(hls_client.get(f"/playlist.m3u8?_HLS_msn={i}") for i in range(6))
    )
    for sequence in range(3, 6):
        await hls_sync.wait_for_handler()
        segment = Segment(sequence=sequence, duration=SEGMENT_DURATION)
        hls.put(segment)

    msn_responses = await msn_requests
    assert msn_responses[0].status == HTTPStatus.OK
    assert msn_responses[1].status == HTTPStatus.OK
    assert msn_responses[2].status == HTTPStatus.OK
    assert msn_responses[3].status == HTTPStatus.OK
    assert msn_responses[4].status == HTTPStatus.OK
    assert msn_responses[5].status == HTTPStatus.BAD_REQUEST

    stream_worker_sync.resume()