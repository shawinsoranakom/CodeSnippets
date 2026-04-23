async def test_pts_out_of_order(hass: HomeAssistant) -> None:
    """Test pts can be out of order and still be valid."""

    # Create a sequence of packets with some out of order pts
    packets = list(PacketSequence(TEST_SEQUENCE_LENGTH))
    for i, _ in enumerate(packets):
        if i % PACKETS_PER_SEGMENT == 1:
            packets[i].pts = packets[i - 1].pts - 1
            packets[i].is_keyframe = False

    decoded_stream = await async_decode_stream(hass, packets)
    segments = decoded_stream.segments
    complete_segments = decoded_stream.complete_segments
    # Check number of segments
    assert len(complete_segments) == int(
        (TEST_SEQUENCE_LENGTH - 1) * SEGMENTS_PER_PACKET
    )
    # Check sequence numbers
    assert all(segments[i].sequence == i for i in range(len(segments)))
    # Check segment durations
    assert all(s.duration == SEGMENT_DURATION for s in complete_segments)
    assert len(decoded_stream.video_packets) == len(packets)
    assert len(decoded_stream.audio_packets) == 0