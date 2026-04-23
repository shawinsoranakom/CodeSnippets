def remux_with_audio(source, container_format, audio_codec):
    """Remux an existing source with new audio."""
    av_source = av.open(source, mode="r")
    output = io.BytesIO()
    output.name = "test.mov" if container_format == "mov" else "test.mp4"
    container = av.open(output, mode="w", format=container_format)
    container.add_stream_from_template(av_source.streams.video[0])

    a_packet = None
    last_a_dts = -1
    if audio_codec is not None:
        if audio_codec == "empty":  # empty we add a stream but don't mux any audio
            astream = container.add_stream("aac", AUDIO_SAMPLE_RATE)
        else:
            astream = container.add_stream(audio_codec, AUDIO_SAMPLE_RATE)
            # Need to do it multiple times for some reason
            while not a_packet:
                a_packets = astream.encode(
                    generate_audio_frame(pcm_mulaw=audio_codec == "pcm_mulaw")
                )
                if a_packets:
                    a_packet = a_packets[0]

    # open original source and iterate through video packets
    for packet in av_source.demux(video=0):
        if not packet.dts:
            continue
        container.mux(packet)
        if a_packet is not None:
            a_packet.pts = int(packet.dts * packet.time_base / a_packet.time_base)
            while (
                a_packet.pts * a_packet.time_base
                < (packet.dts + packet.duration) * packet.time_base
            ):
                a_packet.dts = a_packet.pts
                if (
                    a_packet.dts > last_a_dts
                ):  # avoid writing same dts twice in case of rounding
                    container.mux(a_packet)
                    last_a_dts = a_packet.dts
                a_packet.pts += a_packet.duration

    # Close the file
    container.close()
    output.seek(0)

    return output