async def handle(
        self, request: web.Request, stream: Stream, sequence: str, part_num: str
    ) -> web.Response:
        """Return m3u8 playlist."""
        track: HlsStreamOutput = cast(
            HlsStreamOutput, stream.add_provider(HLS_PROVIDER)
        )
        await stream.start()

        hls_msn: str | int | None = request.query.get("_HLS_msn")
        hls_part: str | int | None = request.query.get("_HLS_part")
        blocking_request = bool(hls_msn or hls_part)

        # If the Playlist URI contains an _HLS_part directive but no _HLS_msn
        # directive, the Server MUST return Bad Request, such as HTTP 400.
        if hls_msn is None and hls_part:
            return web.HTTPBadRequest()

        hls_msn = int(hls_msn or 0)

        # If the _HLS_msn is greater than the Media Sequence Number of the last
        # Media Segment in the current Playlist plus two, or if the _HLS_part
        # exceeds the last Part Segment in the current Playlist by the
        # Advance Part Limit, then the server SHOULD immediately return Bad
        # Request, such as HTTP 400.
        if hls_msn > track.last_sequence + 2:
            return self.bad_request(blocking_request, track.target_duration)

        if hls_part is None:
            # We need to wait for the whole segment, so effectively the next msn
            hls_part = -1
            hls_msn += 1
        else:
            hls_part = int(hls_part)

        while hls_msn > track.last_sequence:
            if not await track.recv():
                return self.not_found(blocking_request, track.target_duration)
        if track.last_segment is None:
            return self.not_found(blocking_request, 0)
        if (
            (last_segment := track.last_segment)
            and hls_msn == last_segment.sequence
            and hls_part
            >= len(last_segment.parts)
            - 1
            + track.stream_settings.hls_advance_part_limit
        ):
            return self.bad_request(blocking_request, track.target_duration)

        # Receive parts until msn and part are met
        while (
            (last_segment := track.last_segment)
            and hls_msn == last_segment.sequence
            and hls_part >= len(last_segment.parts)
        ):
            if not await track.part_recv(
                timeout=track.stream_settings.hls_part_timeout
            ):
                return self.not_found(blocking_request, track.target_duration)
        # Now we should have msn.part >= hls_msn.hls_part. However, in the case
        # that we have a rollover part request from the previous segment, we need
        # to make sure that the new segment has a part. From 6.2.5.2 of the RFC:
        # If the Client requests a Part Index greater than that of the final
        # Partial Segment of the Parent Segment, the Server MUST treat the
        # request as one for Part Index 0 of the following Parent Segment.
        if hls_msn + 1 == last_segment.sequence:
            if not (previous_segment := track.get_segment(hls_msn)) or (
                hls_part >= len(previous_segment.parts)
                and not last_segment.parts
                and not await track.part_recv(
                    timeout=track.stream_settings.hls_part_timeout
                )
            ):
                return self.not_found(blocking_request, track.target_duration)

        response = web.Response(
            body=self.render(track).encode("utf-8"),
            headers={
                "Content-Type": FORMAT_CONTENT_TYPE[HLS_PROVIDER],
            },
        )
        response.enable_compression(web.ContentCoding.gzip)
        return response