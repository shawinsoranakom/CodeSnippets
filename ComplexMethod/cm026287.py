async def get(
        self, request: web.Request, nvr_id: str, camera_id: str, start: str, end: str
    ) -> web.StreamResponse:
        """Get Camera Video clip."""

        data = self._get_data_or_404(nvr_id)
        if isinstance(data, web.Response):
            return data

        camera = self._async_get_camera(data, camera_id)
        if camera is None:
            return _404(f"Invalid camera ID: {camera_id}")
        if not camera.can_read_media(data.api.bootstrap.auth_user):
            return _403(f"User cannot read media from camera: {camera.id}")

        try:
            start_dt = datetime.fromisoformat(start)
        except ValueError:
            return _400("Invalid start")

        try:
            end_dt = datetime.fromisoformat(end)
        except ValueError:
            return _400("Invalid end")

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
            await camera.get_video(start_dt, end_dt, iterator_callback=iterator)
        except ClientError as err:
            return _404(err)

        if response.prepared:
            await response.write_eof()
        return response