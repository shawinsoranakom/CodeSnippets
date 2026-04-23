async def async_play_media(
        self, media_type: MediaType | str, media_id: str, **kwargs: Any
    ) -> None:
        """Send the play_media command to the media player."""
        # If input (file) has a file format supported by pyatv, then stream it with
        # RAOP. Otherwise try to play it with regular AirPlay.
        if not self.atv:
            return
        if media_type in {MediaType.APP, MediaType.URL}:
            await self.atv.apps.launch_app(media_id)
            return

        if media_source.is_media_source_id(media_id):
            play_item = await media_source.async_resolve_media(
                self.hass, media_id, self.entity_id
            )
            media_id = async_process_play_media_url(self.hass, play_item.url)
            media_type = MediaType.MUSIC

        if self._is_feature_available(FeatureName.StreamFile) and (
            media_type == MediaType.MUSIC or await is_streamable(media_id)
        ):
            _LOGGER.debug("Streaming %s via RAOP", media_id)
            await self.atv.stream.stream_file(media_id)
        elif self._is_feature_available(FeatureName.PlayUrl):
            _LOGGER.debug("Playing %s via AirPlay", media_id)
            await self.atv.stream.play_url(media_id)
        else:
            _LOGGER.error("Media streaming is not possible with current configuration")