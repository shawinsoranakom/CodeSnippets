def get_metadata(
        container: "av.container.InputContainer",
    ) -> VideoSourceMetadata:
        if not container.streams.video:
            raise ValueError("No video streams found in container")
        stream = container.streams.video[0]
        total_frames = stream.frames or 0
        fps = float(stream.average_rate) if stream.average_rate else 0.0
        duration = float(stream.duration * stream.time_base) if stream.duration else 0.0
        if total_frames == 0 and duration > 0 and fps > 0:
            total_frames = int(duration * fps)
        return VideoSourceMetadata(total_frames, fps, duration)