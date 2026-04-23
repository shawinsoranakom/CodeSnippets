async def test_get_part_segments(
    hass: HomeAssistant, hls_stream, stream_worker_sync, hls_sync
) -> None:
    """Test requests for part segments and hinted parts."""
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
    segment = create_segment(sequence=0)
    hls.put(segment)
    for part in create_parts(SEQUENCE_BYTES):
        segment.async_add_part(part, 0)
        hls.part_put()
    complete_segment(segment)

    segment = create_segment(sequence=1)
    hls.put(segment)
    remaining_parts = create_parts(SEQUENCE_BYTES)
    num_completed_parts = len(remaining_parts) // 2
    for _ in range(num_completed_parts):
        segment.async_add_part(remaining_parts.pop(0), 0)

    # Make requests for all the existing part segments
    # These should succeed
    requests = asyncio.gather(
        *(
            hls_client.get(f"/segment/1.{part}.m4s")
            for part in range(num_completed_parts)
        )
    )
    responses = await requests
    assert all(response.status == HTTPStatus.OK for response in responses)
    assert all(
        [
            await responses[i].read() == segment.parts[i].data
            for i in range(len(responses))
        ]
    )

    # Request for next segment which has not yet been hinted (we will only hint
    # for this segment after segment 1 is complete).
    # This should fail, but it will hold for one more part_put before failing.
    hls_sync.reset_request_pool(1)
    request = asyncio.create_task(hls_client.get("/segment/2.0.m4s"))
    await hls_sync.wait_for_handler()
    hls.part_put()
    response = await request
    assert response.status == HTTPStatus.NOT_FOUND

    # Put the remaining parts and complete the segment
    while remaining_parts:
        await hls_sync.wait_for_handler()
        # Put one more part segment
        segment.async_add_part(remaining_parts.pop(0), 0)
        hls.part_put()
    complete_segment(segment)

    # Now the hint should have moved to segment 2
    # The request for segment 2 which failed before should work now
    hls_sync.reset_request_pool(1)
    request = asyncio.create_task(hls_client.get("/segment/2.0.m4s"))
    # Put an entire segment and its parts.
    segment = create_segment(sequence=2)
    hls.put(segment)
    remaining_parts = create_parts(ALT_SEQUENCE_BYTES)
    for part in remaining_parts:
        await hls_sync.wait_for_handler()
        segment.async_add_part(part, 0)
        hls.part_put()
    complete_segment(segment)
    # Check the response
    response = await request
    assert response.status == HTTPStatus.OK
    assert (
        await response.read()
        == ALT_SEQUENCE_BYTES[: len(hls.get_segment(2).parts[0].data)]
    )

    stream_worker_sync.resume()