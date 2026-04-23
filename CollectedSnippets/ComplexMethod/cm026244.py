async def async_play_media(
        self, media_type: MediaType | str, media_id: str, **kwargs: Any
    ) -> None:
        """Play a piece of media."""
        LOGGER.debug(
            "async_play_media: type=%s, id=%s, kwargs=%s", media_type, media_id, kwargs
        )
        target_device = self._get_command_target_device("play_media")

        if media_source.is_media_source_id(media_id):
            play_item = await media_source.async_resolve_media(
                self.hass, media_id, self.entity_id
            )
            await self._async_play_url(target_device, play_item.url)
        elif media_type == MEDIA_TYPE_WIIM_LIBRARY:
            if not media_id.isdigit():
                raise ServiceValidationError(f"Invalid preset ID: {media_id}")

            preset_number = int(media_id)
            await target_device.play_preset(preset_number)
            self._attr_media_content_id = f"wiim_preset_{preset_number}"
            self._attr_media_content_type = MediaType.PLAYLIST
            self._attr_state = MediaPlayerState.PLAYING
        elif media_type == MediaType.MUSIC:
            if media_id.isdigit():
                preset_number = int(media_id)
                await target_device.play_preset(preset_number)
                self._attr_media_content_id = f"wiim_preset_{preset_number}"
                self._attr_media_content_type = MediaType.PLAYLIST
                self._attr_state = MediaPlayerState.PLAYING
            else:
                await self._async_play_url(target_device, media_id)
        elif media_type == MediaType.URL:
            await self._async_play_url(target_device, media_id)
        elif media_type == MediaType.TRACK:
            if not media_id.isdigit():
                raise ServiceValidationError(
                    f"Invalid media_id: {media_id}. Expected a valid track index."
                )

            track_index = int(media_id)
            await target_device.async_play_queue_with_index(track_index)
            self._attr_media_content_id = f"wiim_track_{track_index}"
            self._attr_media_content_type = MediaType.TRACK
            self._attr_state = MediaPlayerState.PLAYING
        else:
            raise ServiceValidationError(f"Unsupported media type: {media_type}")