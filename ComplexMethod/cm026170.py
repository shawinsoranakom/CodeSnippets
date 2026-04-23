async def async_browse_media(self, media_content_type=None, media_content_id=None):
        """Implement the websocket media browsing helper."""
        if media_content_id and media_source.is_media_source_id(media_content_id):
            return await media_source.async_browse_media(
                self.hass,
                media_content_id,
                content_filter=lambda item: item.media_content_type.startswith(
                    "audio/"
                ),
            )

        if self.state == MediaPlayerState.OFF:
            raise HomeAssistantError(
                "The device has to be turned on to be able to browse media."
            )

        if media_content_id:
            media_content_path = media_content_id.split(":")
            media_content_provider = await MusicCastMediaContent.browse_media(
                self.coordinator.musiccast, self._zone_id, media_content_path, 24
            )
            add_media_source = False

        else:
            media_content_provider = MusicCastMediaContent.categories(
                self.coordinator.musiccast, self._zone_id
            )
            add_media_source = True

        def get_content_type(item):
            if item.can_play:
                return MediaClass.TRACK
            return MediaClass.DIRECTORY

        children = [
            BrowseMedia(
                title=child.title,
                media_class=MEDIA_CLASS_MAPPING.get(child.content_type),
                media_content_id=child.content_id,
                media_content_type=get_content_type(child),
                can_play=child.can_play,
                can_expand=child.can_browse,
                thumbnail=child.thumbnail,
            )
            for child in media_content_provider.children
        ]

        if add_media_source:
            with contextlib.suppress(BrowseError):
                item = await media_source.async_browse_media(
                    self.hass,
                    None,
                    content_filter=lambda item: item.media_content_type.startswith(
                        "audio/"
                    ),
                )
                # If domain is None, it's overview of available sources
                if item.domain is None:
                    children.extend(item.children)
                else:
                    children.append(item)

        return BrowseMedia(
            title=media_content_provider.title,
            media_class=MEDIA_CLASS_MAPPING.get(media_content_provider.content_type),
            media_content_id=media_content_provider.content_id,
            media_content_type=get_content_type(media_content_provider),
            can_play=False,
            can_expand=media_content_provider.can_browse,
            children=children,
        )