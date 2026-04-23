def write_segment(segment: Segment) -> None:
            """Write a segment to output."""
            # fmt: off
            nonlocal output, output_v, output_a, last_stream_id, running_duration, last_sequence
            # fmt: on
            # Because the stream_worker is in a different thread from the record service,
            # the lookback segments may still have some overlap with the recorder segments
            if segment.sequence <= last_sequence:
                return
            last_sequence = segment.sequence

            # Open segment
            source = av.open(
                BytesIO(segment.init + segment.get_data()),
                "r",
                format=SEGMENT_CONTAINER_FORMAT,
            )
            # Skip this segment if it doesn't have data
            if source.duration is None:
                source.close()
                return
            source_v = source.streams.video[0]
            source_a = (
                source.streams.audio[0] if len(source.streams.audio) > 0 else None
            )

            # Create output on first segment
            if not output:
                container_options: dict[str, str] = {
                    "video_track_timescale": str(int(1 / source_v.time_base)),  # type: ignore[operator]
                    "movflags": "frag_keyframe+empty_moov",
                    "min_frag_duration": str(self.stream_settings.min_segment_duration),
                }
                output = av.open(
                    self.video_path + ".tmp",
                    "w",
                    format=RECORDER_CONTAINER_FORMAT,
                    container_options=container_options,
                )

            # Add output streams if necessary
            if not output_v:
                output_v = output.add_stream_from_template(source_v)
            if source_a and not output_a:
                output_a = output.add_stream_from_template(source_a)

            # Recalculate pts adjustments on first segment and on any discontinuity
            # We are assuming time base is the same across all discontinuities
            if last_stream_id != segment.stream_id:
                last_stream_id = segment.stream_id
                pts_adjuster["video"] = int(
                    (running_duration - source.start_time)
                    / (av.time_base * source_v.time_base)  # type: ignore[operator]
                )
                if source_a:
                    pts_adjuster["audio"] = int(
                        (running_duration - source.start_time)
                        / (av.time_base * source_a.time_base)  # type: ignore[operator]
                    )

            # Remux video
            for packet in source.demux():
                if packet.pts is None:
                    continue
                packet.pts += pts_adjuster[packet.stream.type]  # type: ignore[operator]
                packet.dts += pts_adjuster[packet.stream.type]  # type: ignore[operator]
                stream = output_v if packet.stream.type == "video" else output_a
                assert stream
                packet.stream = stream
                output.mux(packet)

            running_duration += source.duration - source.start_time

            source.close()