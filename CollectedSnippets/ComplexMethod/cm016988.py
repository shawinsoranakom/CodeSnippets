def trim_video(video: Input.Video, duration_sec: float) -> Input.Video:
    """
    Returns a new VideoInput object trimmed from the beginning to the specified duration,
    using av to avoid loading entire video into memory.

    Args:
        video: Input video to trim
        duration_sec: Duration in seconds to keep from the beginning

    Returns:
        VideoFromFile object that owns the output buffer
    """
    output_buffer = BytesIO()
    input_container = None
    output_container = None

    try:
        # Get the stream source - this avoids loading entire video into memory
        # when the source is already a file path
        input_source = video.get_stream_source()

        # Open containers
        input_container = av.open(input_source, mode="r")
        output_container = av.open(output_buffer, mode="w", format="mp4")

        # Set up output streams for re-encoding
        video_stream = None
        audio_stream = None

        for stream in input_container.streams:
            logging.info("Found stream: type=%s, class=%s", stream.type, type(stream))
            if isinstance(stream, av.VideoStream):
                # Create output video stream with same parameters
                video_stream = output_container.add_stream("h264", rate=stream.average_rate)
                video_stream.width = stream.width
                video_stream.height = stream.height
                video_stream.pix_fmt = "yuv420p"
                logging.info("Added video stream: %sx%s @ %sfps", stream.width, stream.height, stream.average_rate)
            elif isinstance(stream, av.AudioStream):
                # Create output audio stream with same parameters
                audio_stream = output_container.add_stream("aac", rate=stream.sample_rate)
                audio_stream.sample_rate = stream.sample_rate
                audio_stream.layout = stream.layout
                logging.info("Added audio stream: %sHz, %s channels", stream.sample_rate, stream.channels)

        # Calculate target frame count that's divisible by 16
        fps = input_container.streams.video[0].average_rate
        estimated_frames = int(duration_sec * fps)
        target_frames = (estimated_frames // 16) * 16  # Round down to nearest multiple of 16

        if target_frames == 0:
            raise ValueError("Video too short: need at least 16 frames for Moonvalley")

        frame_count = 0
        audio_frame_count = 0

        # Decode and re-encode video frames
        if video_stream:
            for frame in input_container.decode(video=0):
                if frame_count >= target_frames:
                    break

                # Re-encode frame
                for packet in video_stream.encode(frame):
                    output_container.mux(packet)
                frame_count += 1

            # Flush encoder
            for packet in video_stream.encode():
                output_container.mux(packet)

            logging.info("Encoded %s video frames (target: %s)", frame_count, target_frames)

        # Decode and re-encode audio frames
        if audio_stream:
            input_container.seek(0)  # Reset to beginning for audio
            for frame in input_container.decode(audio=0):
                if frame.time >= duration_sec:
                    break

                # Re-encode frame
                for packet in audio_stream.encode(frame):
                    output_container.mux(packet)
                audio_frame_count += 1

            # Flush encoder
            for packet in audio_stream.encode():
                output_container.mux(packet)

            logging.info("Encoded %s audio frames", audio_frame_count)

        # Close containers
        output_container.close()
        input_container.close()

        # Return as VideoFromFile using the buffer
        output_buffer.seek(0)
        return InputImpl.VideoFromFile(output_buffer)

    except Exception as e:
        # Clean up on error
        if input_container is not None:
            input_container.close()
        if output_container is not None:
            output_container.close()
        raise RuntimeError(f"Failed to trim video: {str(e)}") from e