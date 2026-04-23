async def async_play_media(
        self, media_type: MediaType | str, media_id: str, **kwargs: Any
    ) -> None:
        """Play a piece of media."""
        if heos_source.is_media_uri(media_id):
            media, _data = heos_source.from_media_uri(media_id)
            if not isinstance(media, MediaItem):
                raise ValueError(f"Invalid media id '{media_id}'")
            await self._player.play_media(
                media,
                HA_HEOS_ENQUEUE_MAP[kwargs.get(ATTR_MEDIA_ENQUEUE)],
            )
            return

        if media_source.is_media_source_id(media_id):
            media_type = MediaType.URL
            play_item = await media_source.async_resolve_media(
                self.hass, media_id, self.entity_id
            )
            media_id = play_item.url

        if media_type in {MediaType.URL, MediaType.MUSIC}:
            media_id = async_process_play_media_url(self.hass, media_id)

            await self._player.play_url(media_id)
            return

        if media_type == "quick_select":
            # media_id may be an int or a str
            selects = await self._player.get_quick_selects()
            try:
                index: int | None = int(media_id)
            except ValueError:
                # Try finding index by name
                index = next(
                    (index for index, select in selects.items() if select == media_id),
                    None,
                )
            if index is None:
                raise ValueError(f"Invalid quick select '{media_id}'")
            await self._player.play_quick_select(index)
            return

        if media_type == MediaType.PLAYLIST:
            playlists = await self.coordinator.heos.get_playlists()
            playlist = next((p for p in playlists if p.name == media_id), None)
            if not playlist:
                raise ValueError(f"Invalid playlist '{media_id}'")
            add_queue_option = HA_HEOS_ENQUEUE_MAP[kwargs.get(ATTR_MEDIA_ENQUEUE)]
            await self._player.play_media(playlist, add_queue_option)
            return

        if media_type == "favorite":
            # media_id may be an int or str
            try:
                index = int(media_id)
            except ValueError:
                # Try finding index by name
                index = self.coordinator.async_get_favorite_index(media_id)
            if index is None:
                raise ValueError(f"Invalid favorite '{media_id}'")
            await self._player.play_preset_station(index)
            return

        if media_type == "queue":
            # media_id must be an int
            try:
                queue_id = int(media_id)
            except ValueError:
                raise ValueError(f"Invalid queue id '{media_id}'") from None
            await self._player.play_queue(queue_id)
            return

        raise ValueError(f"Unsupported media type '{media_type}'")