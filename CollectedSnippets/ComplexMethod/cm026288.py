async def get(
        self, request: web.Request, nvr_id: str, event_id: str
    ) -> web.StreamResponse:
        """Get Camera Video clip for an event."""

        data = self._get_data_or_404(nvr_id)
        if isinstance(data, web.Response):
            return data

        try:
            event = await data.api.get_event(event_id)
        except ClientError:
            return _404(f"Invalid event ID: {event_id}")
        if event.start is None or event.end is None:
            return _400("Event is still ongoing")
        camera = self._async_get_camera(data, str(event.camera_id))
        if camera is None:
            return _404(f"Invalid camera ID: {event.camera_id}")
        if not camera.can_read_media(data.api.bootstrap.auth_user):
            return _403(f"User cannot read media from camera: {camera.id}")

        response = web.StreamResponse(
            status=200,
            reason="OK",
            headers={
                "Content-Type": "video/mp4",
            },
        )

        async def iterator(total: int, chunk: bytes | None) -> None:
            if not response.prepared:
                response.content_length = total
                await response.prepare(request)

            if chunk is not None:
                await response.write(chunk)

        try:
            await camera.get_video(event.start, event.end, iterator_callback=iterator)
        except ClientError as err:
            return _404(err)

        if response.prepared:
            await response.write_eof()
        return response