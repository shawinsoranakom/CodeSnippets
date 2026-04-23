async def async_browse_media(
        self,
        media_content_type: MediaType | str | None = None,
        media_content_id: str | None = None,
    ) -> BrowseMedia:
        """Implement media Browse helper."""
        LOGGER.debug(
            "Browsing media: content_type=%s, content_id=%s",
            media_content_type,
            media_content_id,
        )

        if media_content_id is not None and media_source.is_media_source_id(
            media_content_id
        ):
            if not self._device.supports_http_api:
                raise BrowseError("Media sources are not supported on this device")

            return await media_source.async_browse_media(
                self.hass,
                media_content_id,
                content_filter=lambda item: item.media_content_type.startswith(
                    "audio/"
                ),
            )

        # Root browse
        if media_content_id is None or media_content_id == MEDIA_CONTENT_ID_ROOT:
            children: list[BrowseMedia] = []
            children.append(
                BrowseMedia(
                    media_class=MediaClass.DIRECTORY,
                    media_content_id=MEDIA_CONTENT_ID_FAVORITES,
                    media_content_type=MediaType.PLAYLIST,
                    title="Presets",
                    can_play=False,
                    can_expand=True,
                    thumbnail=None,
                ),
            )
            children.append(
                BrowseMedia(
                    media_class=MediaClass.DIRECTORY,
                    media_content_id=MEDIA_CONTENT_ID_PLAYLISTS,
                    media_content_type=MediaType.PLAYLIST,
                    title="Queue",
                    can_play=False,
                    can_expand=True,
                    thumbnail=None,
                ),
            )
            if self._device.supports_http_api:
                media_sources_item = await media_source.async_browse_media(
                    self.hass,
                    None,
                    content_filter=lambda item: item.media_content_type.startswith(
                        "audio/"
                    ),
                )

                if media_sources_item.children:
                    children.extend(media_sources_item.children)

            return BrowseMedia(
                media_class=MediaClass.DIRECTORY,
                media_content_id=MEDIA_CONTENT_ID_ROOT,
                media_content_type=MEDIA_TYPE_WIIM_LIBRARY,
                title=self._device.name,
                can_play=False,
                can_expand=True,
                children=children,
            )

        if media_content_id == MEDIA_CONTENT_ID_FAVORITES:
            sdk_favorites = await self._device.async_get_presets()
            favorites_items = [
                BrowseMedia(
                    media_class=MediaClass.PLAYLIST,
                    media_content_id=str(item.preset_id),
                    media_content_type=MediaType.MUSIC,
                    title=item.title,
                    can_play=True,
                    can_expand=False,
                    thumbnail=item.image_url,
                )
                for item in sdk_favorites
            ]

            return BrowseMedia(
                media_class=MediaClass.PLAYLIST,
                media_content_id=MEDIA_CONTENT_ID_FAVORITES,
                media_content_type=MediaType.PLAYLIST,
                title="Presets",
                can_play=False,
                can_expand=True,
                children=favorites_items,
            )

        if media_content_id == MEDIA_CONTENT_ID_PLAYLISTS:
            queue_snapshot = await self._device.async_get_queue_snapshot()
            if not queue_snapshot.is_active:
                return BrowseMedia(
                    media_class=MediaClass.PLAYLIST,
                    media_content_id=MEDIA_CONTENT_ID_PLAYLISTS,
                    media_content_type=MediaType.PLAYLIST,
                    title="Queue",
                    can_play=False,
                    can_expand=True,
                    children=[],
                )

            playlist_track_items = [
                BrowseMedia(
                    media_class=MediaClass.TRACK,
                    media_content_id=str(item.queue_index),
                    media_content_type=MediaType.TRACK,
                    title=item.title,
                    can_play=True,
                    can_expand=False,
                    thumbnail=item.image_url,
                )
                for item in queue_snapshot.items
            ]

            return BrowseMedia(
                media_class=MediaClass.PLAYLIST,
                media_content_id=MEDIA_CONTENT_ID_PLAYLISTS,
                media_content_type=MediaType.PLAYLIST,
                title="Queue",
                can_play=False,
                can_expand=True,
                children=playlist_track_items,
            )

        LOGGER.warning(
            "Unhandled browse_media request: content_type=%s, content_id=%s",
            media_content_type,
            media_content_id,
        )
        raise BrowseError(f"Invalid browse path: {media_content_id}")