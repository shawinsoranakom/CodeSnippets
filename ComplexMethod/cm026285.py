async def get(
        self, request: web.Request, nvr_id: str, event_id: str
    ) -> web.Response:
        """Get Event Thumbnail."""

        data = self._get_data_or_404(nvr_id)
        if isinstance(data, web.Response):
            return data

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
            thumbnail = await data.api.get_event_thumbnail(
                event_id, width=width, height=height
            )
        except ClientError as err:
            return _404(err)

        if thumbnail is None:
            return _404("Event thumbnail not found")

        return web.Response(body=thumbnail, content_type="image/jpeg")