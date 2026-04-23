async def async_resolve_media(self, item: MediaSourceItem) -> PlayMedia:
        """Return a streamable URL and associated mime type for a UniFi Protect event.

        Accepted identifier format are

        * {nvr_id}:event:{event_id} - MP4 video clip for specific event
        * {nvr_id}:eventthumb:{event_id} - Thumbnail JPEG for specific event
        """

        parts = item.identifier.split(":")
        if len(parts) != 3 or parts[1] not in ("event", "eventthumb"):
            _bad_identifier(item.identifier)

        thumbnail_only = parts[1] == "eventthumb"
        try:
            data = self.data_sources[parts[0]]
        except (KeyError, IndexError) as err:
            _bad_identifier(item.identifier, err)

        event = data.api.bootstrap.events.get(parts[2])
        if event is None:
            try:
                event = await data.api.get_event(parts[2])
            except NvrError as err:
                _bad_identifier(item.identifier, err)
            else:
                # cache the event for later
                data.api.bootstrap.events[event.id] = event

        nvr = data.api.bootstrap.nvr
        if thumbnail_only:
            return PlayMedia(
                async_generate_thumbnail_url(event.id, nvr.id), "image/jpeg"
            )
        return PlayMedia(async_generate_event_video_url(event), "video/mp4")