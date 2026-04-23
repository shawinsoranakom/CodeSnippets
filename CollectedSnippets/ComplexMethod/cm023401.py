async def test_skip_out_of_order_packet(hass: HomeAssistant) -> None:
    """Skip a single out of order packet."""
    packets = list(PacketSequence(TEST_SEQUENCE_LENGTH))
    # for this test, make sure the out of order index doesn't happen on a keyframe
    out_of_order_index = OUT_OF_ORDER_PACKET_INDEX
    if packets[out_of_order_index].is_keyframe:
        out_of_order_index += 1
    # This packet is out of order
    assert not packets[out_of_order_index].is_keyframe
    packets[out_of_order_index].dts = -9090

    decoded_stream = await async_decode_stream(hass, packets)
    segments = decoded_stream.segments
    complete_segments = decoded_stream.complete_segments
    # Check sequence numbers
    assert all(segments[i].sequence == i for i in range(len(segments)))
    # If skipped packet would have been the first packet of a segment, the previous
    # segment will be longer by a packet duration
    # We also may possibly lose a segment due to the shifting pts boundary
    if out_of_order_index % PACKETS_PER_SEGMENT == 0:
        # Check duration of affected segment and remove it
        longer_segment_index = int((out_of_order_index - 1) * SEGMENTS_PER_PACKET)
        assert (
            segments[longer_segment_index].duration
            == SEGMENT_DURATION + PACKET_DURATION
        )
        del segments[longer_segment_index]
        # Check number of segments
        assert len(complete_segments) == int(
            (len(packets) - 1 - 1) * SEGMENTS_PER_PACKET - 1
        )
    else:  # Otherwise segment durations and number of segments are unaffected
        # Check number of segments
        assert len(complete_segments) == int((len(packets) - 1) * SEGMENTS_PER_PACKET)
    # Check remaining segment durations
    assert all(s.duration == SEGMENT_DURATION for s in complete_segments)
    assert len(decoded_stream.video_packets) == len(packets) - 1
    assert len(decoded_stream.audio_packets) == 0