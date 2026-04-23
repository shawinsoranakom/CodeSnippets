def _apply_video_scale(video: Input.Video, scale_dims: tuple[int, int]) -> Input.Video:
    """Re-encode ``video`` scaled to ``scale_dims`` with a single decode/encode pass."""
    out_w, out_h = scale_dims
    output_buffer = BytesIO()
    input_container = None
    output_container = None

    try:
        input_source = video.get_stream_source()
        input_container = av.open(input_source, mode="r")
        output_container = av.open(output_buffer, mode="w", format="mp4")

        video_stream = output_container.add_stream("h264", rate=video.get_frame_rate())
        video_stream.width = out_w
        video_stream.height = out_h
        video_stream.pix_fmt = "yuv420p"

        audio_stream = None
        for stream in input_container.streams:
            if isinstance(stream, av.AudioStream):
                audio_stream = output_container.add_stream("aac", rate=stream.sample_rate)
                audio_stream.sample_rate = stream.sample_rate
                audio_stream.layout = stream.layout
                break

        for frame in input_container.decode(video=0):
            frame = frame.reformat(width=out_w, height=out_h, format="yuv420p")
            for packet in video_stream.encode(frame):
                output_container.mux(packet)
        for packet in video_stream.encode():
            output_container.mux(packet)

        if audio_stream is not None:
            input_container.seek(0)
            for audio_frame in input_container.decode(audio=0):
                for packet in audio_stream.encode(audio_frame):
                    output_container.mux(packet)
            for packet in audio_stream.encode():
                output_container.mux(packet)

        output_container.close()
        input_container.close()
        output_buffer.seek(0)
        return InputImpl.VideoFromFile(output_buffer)

    except Exception as e:
        if input_container is not None:
            input_container.close()
        if output_container is not None:
            output_container.close()
        raise RuntimeError(f"Failed to resize video: {str(e)}") from e