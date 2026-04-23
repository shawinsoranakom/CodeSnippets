async def get(
        self, request: Request, source_dir_id: str, location: str
    ) -> Response | StreamResponse:
        """Start a GET request."""
        if not self.hass.config_entries.async_loaded_entries(DOMAIN):
            raise HTTPNotFound

        try:
            asset_id, size, mime_type_base, mime_type_format = location.split("/")
        except ValueError as err:
            raise HTTPNotFound from err

        entry: ImmichConfigEntry | None = (
            self.hass.config_entries.async_entry_for_domain_unique_id(
                DOMAIN, source_dir_id
            )
        )
        assert entry
        immich_api = entry.runtime_data.api

        # stream response for videos
        if mime_type_base == "video":
            try:
                resp = await immich_api.assets.async_play_video_stream(asset_id)
            except ImmichError as exc:
                raise HTTPNotFound from exc
            stream = ChunkAsyncStreamIterator(resp)
            response = StreamResponse()
            await response.prepare(request)
            async for chunk in stream:
                await response.write(chunk)
            return response

        # web response for images
        try:
            if size == "person":
                image = await immich_api.people.async_get_person_thumbnail(asset_id)
            else:
                image = await immich_api.assets.async_view_asset(asset_id, size)
        except ImmichError as exc:
            raise HTTPNotFound from exc
        return Response(body=image, content_type=f"{mime_type_base}/{mime_type_format}")