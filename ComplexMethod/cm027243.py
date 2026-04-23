async def async_play_media(
        self,
        media_type: MediaType | str,
        media_id: str,
        announce: bool | None = None,
        **kwargs: Any,
    ) -> None:
        """Send the play_media command to the media player."""
        index = None

        if media_type:
            media_type = media_type.lower()

        enqueue: MediaPlayerEnqueue | None = kwargs.get(ATTR_MEDIA_ENQUEUE)

        if enqueue == MediaPlayerEnqueue.ADD:
            cmd = "add"
        elif enqueue == MediaPlayerEnqueue.NEXT:
            cmd = "insert"
        elif enqueue == MediaPlayerEnqueue.PLAY:
            cmd = "play_now"
        else:
            cmd = "play"

        if media_source.is_media_source_id(media_id):
            media_type = MediaType.MUSIC
            play_item = await media_source.async_resolve_media(
                self.hass, media_id, self.entity_id
            )
            media_id = play_item.url

        if announce:
            if media_type not in MediaType.MUSIC:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="invalid_announce_media_type",
                    translation_placeholders={"media_type": str(media_type)},
                )

            extra = kwargs.get(ATTR_MEDIA_EXTRA, {})
            cmd = "announce"
            try:
                announce_volume = get_announce_volume(extra)
            except ValueError:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="invalid_announce_volume",
                    translation_placeholders={"announce_volume": ATTR_ANNOUNCE_VOLUME},
                ) from None
            else:
                self._player.set_announce_volume(announce_volume)

            try:
                announce_timeout = get_announce_timeout(extra)
            except ValueError:
                raise ServiceValidationError(
                    translation_domain=DOMAIN,
                    translation_key="invalid_announce_timeout",
                    translation_placeholders={
                        "announce_timeout": ATTR_ANNOUNCE_TIMEOUT
                    },
                ) from None
            else:
                self._player.set_announce_timeout(announce_timeout)

        if media_type in MediaType.MUSIC:
            if not media_id.startswith(SQUEEZEBOX_SOURCE_STRINGS):
                media_id = async_process_play_media_url(self.hass, media_id)

            await safe_library_call(
                self._player.async_load_url,
                media_id,
                cmd,
                translation_key="load_url_failed",
                translation_placeholders={"media_id": media_id, "cmd": cmd},
            )
            return

        if media_type == MediaType.PLAYLIST:
            try:
                payload = {
                    "search_id": media_id,
                    "search_type": MediaType.PLAYLIST,
                }
                playlist = await generate_playlist(
                    self._player, payload, self.browse_limit, self._browse_data
                )
            except BrowseError:
                content = json.loads(media_id)
                playlist = content["urls"]
                index = content["index"]
        else:
            payload = {
                "search_id": media_id,
                "search_type": media_type,
            }
            playlist = await generate_playlist(
                self._player, payload, self.browse_limit, self._browse_data
            )
            _LOGGER.debug("Generated playlist: %s", playlist)

        await safe_library_call(
            self._player.async_load_playlist,
            playlist,
            cmd,
            translation_key="load_playlist_failed",
            translation_placeholders={"cmd": cmd},
        )

        if index is not None:
            await self._player.async_index(index)

        await self.coordinator.async_refresh()