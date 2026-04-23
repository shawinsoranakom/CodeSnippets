async def async_play_media(
        self, media_type: MediaType | str, media_id: str, **kwargs: Any
    ) -> None:
        """Send the play_media command to the media player.

        If media_id is a Plex payload, attempt Plex->Sonos playback.

        If media_id is an Apple Music, Deezer, Sonos, or Tidal share link,
        attempt playback using the respective service.

        If media_type is "playlist", media_id should be a Sonos
        Playlist name.  Otherwise, media_id should be a URI.
        """
        is_radio = False

        if media_source.is_media_source_id(media_id):
            is_radio = media_id.startswith("media-source://radio_browser/")
            media_type = MediaType.MUSIC
            media = await media_source.async_resolve_media(
                self.hass, media_id, self.entity_id
            )
            media_id = async_process_play_media_url(self.hass, media.url)

        if kwargs.get(ATTR_MEDIA_ANNOUNCE):
            volume = kwargs.get("extra", {}).get("volume")
            _LOGGER.debug("Playing %s using websocket audioclip", media_id)
            try:
                assert self.speaker.websocket
                response, _ = await self.speaker.websocket.play_clip(
                    async_process_play_media_url(self.hass, media_id),
                    volume=volume,
                )
            except SonosWebsocketError as exc:
                raise HomeAssistantError(
                    f"Error when calling Sonos websocket: {exc}"
                ) from exc
            if response.get("success"):
                return
            if response.get("type") in ANNOUNCE_NOT_SUPPORTED_ERRORS:
                # If the speaker does not support announce do not raise and
                # fall through to_play_media to play the clip directly.
                _LOGGER.debug(
                    "Speaker %s does not support announce, media_id %s response %s",
                    self.speaker.zone_name,
                    media_id,
                    response,
                )
            else:
                raise HomeAssistantError(
                    translation_domain=DOMAIN,
                    translation_key="announce_media_error",
                    translation_placeholders={
                        "media_id": media_id,
                        "response": response,
                    },
                )

        if spotify.is_spotify_media_type(media_type):
            media_type = spotify.resolve_spotify_media_type(media_type)
            media_id = spotify.spotify_uri_from_media_browser_url(media_id)

        await self.hass.async_add_executor_job(
            partial(self._play_media, media_type, media_id, is_radio, **kwargs)
        )