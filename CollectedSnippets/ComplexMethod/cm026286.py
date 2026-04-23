async def get(
        self, request: web.Request, nvr_id: str, camera_id: str, timestamp: str
    ) -> web.Response:
        """Get snapshot."""

        data = self._get_data_or_404(nvr_id)
        if isinstance(data, web.Response):
            return data

        camera = self._async_get_camera(data, camera_id)
        if camera is None:
            return _404(f"Invalid camera ID: {camera_id}")
        if not camera.can_read_media(data.api.bootstrap.auth_user):
            return _403(f"User cannot read media from camera: {camera.id}")

        width: int | str | None = request.query.get("width")
        height: int | str | None = request.query.get("height")

        if width is not None:
            try:
                width = int(width)
            except ValueError:
                return _400("Invalid width param")
        if height is not None:
            try:
                height = int(height)
            except ValueError:
                return _400("Invalid height param")

        try:
            timestamp_dt = datetime.fromisoformat(timestamp)
        except ValueError:
            return _400("Invalid timestamp")

        try:
            snapshot = await camera.get_snapshot(
                width=width, height=height, dt=timestamp_dt
            )
        except ClientError as err:
            return _404(err)

        if snapshot is None:
            return _404("snapshot not found")

        return web.Response(body=snapshot, content_type="image/jpeg")