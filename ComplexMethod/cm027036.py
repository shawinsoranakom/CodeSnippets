def _render_hls_template(self, last_stream_id: int, render_parts: bool) -> str:
        """Render the HLS playlist section for the Segment.

        The Segment may still be in progress.
        This method stores intermediate data in hls_playlist_parts,
        hls_num_parts_rendered, and hls_playlist_complete to avoid redoing
        work on subsequent calls.
        """
        if self.hls_playlist_complete:
            return self.hls_playlist_template[0]
        if not self.hls_playlist_template:
            # Logically EXT-X-DISCONTINUITY makes sense above the parts, but Apple's
            # media stream validator seems to only want it before the segment
            if last_stream_id != self.stream_id:
                self.hls_playlist_template.append("#EXT-X-DISCONTINUITY")
            # This is a placeholder where the rendered parts will be inserted
            self.hls_playlist_template.append("{}")
        if render_parts:
            for part_num, part in enumerate(
                self.parts[self.hls_num_parts_rendered :], self.hls_num_parts_rendered
            ):
                self.hls_playlist_parts.append(
                    f"#EXT-X-PART:DURATION={part.duration:.3f},URI="
                    f'"./segment/{self.sequence}.{part_num}.m4s"'
                    f"{',INDEPENDENT=YES' if part.has_keyframe else ''}"
                )
        if self.complete:
            # Construct the final playlist_template. The placeholder will share a
            # line with the first element to avoid an extra newline when we don't
            # render any parts. Append an empty string to create a trailing newline
            # when we do render parts
            self.hls_playlist_parts.append("")
            self.hls_playlist_template = (
                [] if last_stream_id == self.stream_id else ["#EXT-X-DISCONTINUITY"]
            )
            # Add the remaining segment metadata
            # The placeholder goes on the same line as the next element
            self.hls_playlist_template.extend(
                [
                    "{}#EXT-X-PROGRAM-DATE-TIME:"
                    + self.start_time.strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
                    + "Z",
                    f"#EXTINF:{self.duration:.3f},\n./segment/{self.sequence}.m4s",
                ]
            )

        # Store intermediate playlist data in member variables for reuse
        self.hls_playlist_template = ["\n".join(self.hls_playlist_template)]
        # lstrip discards extra preceding newline in case first render was empty
        self.hls_playlist_parts = ["\n".join(self.hls_playlist_parts).lstrip()]
        self.hls_num_parts_rendered = len(self.parts)
        self.hls_playlist_complete = self.complete

        return self.hls_playlist_template[0]