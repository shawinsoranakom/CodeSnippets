async def async_play_media(
        self, media_type: MediaType | str, media_id: str, **kwargs: Any
    ) -> None:
        """Play a piece of media."""
        chromecast = self._get_chromecast()
        # Handle media_source
        if media_source.is_media_source_id(media_id):
            sourced_media = await media_source.async_resolve_media(
                self.hass, media_id, self.entity_id
            )
            media_type = sourced_media.mime_type
            media_id = sourced_media.url

        extra = kwargs.get(ATTR_MEDIA_EXTRA, {})

        # Handle media supported by a known cast app
        if media_type == DOMAIN:
            try:
                app_data = json.loads(media_id)
                if metadata := extra.get("metadata"):
                    app_data["metadata"] = metadata
            except json.JSONDecodeError:
                _LOGGER.error("Invalid JSON in media_content_id")
                raise

            # Special handling for passed `app_id` parameter. This will only launch
            # an arbitrary cast app, generally for UX.
            if "app_id" in app_data:
                app_id = app_data.pop("app_id")
                _LOGGER.debug("Starting Cast app by ID %s", app_id)
                await self.hass.async_add_executor_job(self._start_app, app_id)
                if app_data:
                    _LOGGER.warning(
                        "Extra keys %s were ignored. Please use app_name to cast media",
                        app_data.keys(),
                    )
                return

            app_name = app_data.pop("app_name")
            try:
                await self.hass.async_add_executor_job(
                    self._quick_play, app_name, app_data
                )
            except NotImplementedError:
                _LOGGER.error("App %s not supported", app_name)
            return

        # Try the cast platforms
        for platform in self.hass.data[DOMAIN]["cast_platform"].values():
            result = await platform.async_play_media(
                self.hass, self.entity_id, chromecast, media_type, media_id
            )
            if result:
                return

        # If media ID is a relative URL, we serve it from HA.
        media_id = async_process_play_media_url(self.hass, media_id)

        # Configure play command for when playing a HLS stream
        if is_hass_url(self.hass, media_id):
            parsed = yarl.URL(media_id)
            if parsed.path.startswith("/api/hls/"):
                extra = {
                    **extra,
                    "stream_type": "LIVE",
                    "media_info": {
                        "hlsVideoSegmentFormat": "fmp4",
                    },
                }
        elif media_id.endswith((".m3u", ".m3u8", ".pls")):
            try:
                playlist = await parse_playlist(self.hass, media_id)
                _LOGGER.debug(
                    "[%s %s] Playing item %s from playlist %s",
                    self.entity_id,
                    self._cast_info.friendly_name,
                    playlist[0].url,
                    media_id,
                )
                media_id = playlist[0].url
                if title := playlist[0].title:
                    extra = {
                        **extra,
                        "metadata": {"title": title},
                    }
            except PlaylistSupported as err:
                _LOGGER.debug(
                    "[%s %s] Playlist %s is supported: %s",
                    self.entity_id,
                    self._cast_info.friendly_name,
                    media_id,
                    err,
                )
            except PlaylistError as err:
                _LOGGER.warning(
                    "[%s %s] Failed to parse playlist %s: %s",
                    self.entity_id,
                    self._cast_info.friendly_name,
                    media_id,
                    err,
                )

        # Default to play with the default media receiver
        app_data = {"media_id": media_id, "media_type": media_type, **extra}
        _LOGGER.debug(
            "[%s %s] Playing %s with default_media_receiver",
            self.entity_id,
            self._cast_info.friendly_name,
            app_data,
        )
        await self.hass.async_add_executor_job(
            self._quick_play, "default_media_receiver", app_data
        )